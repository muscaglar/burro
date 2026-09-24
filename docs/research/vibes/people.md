# people: who lives there, and cultural background

Researched 2026-09-23. A dated snapshot, not a source of truth. I am not a lawyer, and nothing here is legal advice.

## Headline

The founder asked for the local makeup of an area: foreign born, ethnicities, cultural background. The data exists, is free, and is licensed for commercial use. Census 2021 publishes ethnic group, religion, country of birth and household type for areas of 100 to 625 people. The question is not whether Burro may hold the figures. It is what Burro does with them.

Three acts are often treated as one, and they are not alike. **Showing** an official figure on an area page is what the statistics office, the GLA and two commercial sites I read already do, and I found no UK regulator action against it. **Ranking or filtering** by who lives somewhere makes Burro's own code sort places by race or religion. **Building a named vibe** from who lives somewhere attaches a judgement to a group's presence, for every user, by Burro's own recipe. The first is a presentation risk. The second and third are the conduct the fairness rule exists to prevent, and nothing I read today clears them.

My recommendation is to keep residents out of every ranking, filter and vibe, to build "cultural background" from places, and to show census figures on the area page in a fenced panel, in two steps. The decision is the founder's. The default, if nothing is decided, is that ADR 0006 stands as written.

## Summary

| Finding | Detail |
|---|---|
| Census 2021 reaches neighbourhood scale for the broad tables | Ethnic group (19 tick-box groups), religion, country of birth (12 groups), household composition, year of arrival and national identity are all published down to output area |
| The detailed tables do not | Main language and detailed country of birth are published for boroughs only. Detailed ethnic group and detailed religion stop at MSOA. Burro cannot honestly say which languages are spoken in a neighbourhood |
| Licence | Open Government Licence v3.0. Commercial use is allowed. The licence does not cover personal data. Census tables are statistics about areas, already adjusted so that nobody can be picked out |
| Disclosure control | Records are swapped between nearby small areas, and small counts are nudged. A sum over a neighbourhood is sound for large groups and unreliable for small ones |
| Staleness | Census Day was 21 March 2021, in lockdown. At a web launch in late January 2027 the figures are 5 years and 10 months old. The next census is in 2031 |
| What UK services do | Of the pages I opened, two commercial sites show ethnic group by postcode or postcode district, and one of those also shows religion. One site says users can find areas by age bracket. None offered a filter by ethnicity or religion. The area finders and the large portals' home pages mention no resident data |
| Equality Act, Part 3 | On the Code's wording, Burro is a service provider. The EHRC's 2026 Code says an estate agent "advertising or providing information about properties" is providing a service to the public. The duties run to the person using the service |
| Segregation | For race, segregation is automatically less favourable treatment. The Code says it must be "a deliberate act or policy", and that users separating by their own choice is not segregation. A filter by ethnicity that Burro builds sits on that line, unreviewed |
| Area as a stand-in for race | The Code gives an example of a postcode rule that indirectly discriminates. The FCA studied car insurance prices by local-area ethnicity in 2025. UK regulators do look at this |
| Data protection | Census aggregates are outside data protection law. A person's own search is not. If a filter says "areas with more people of my faith", Burro is holding something that reveals the searcher's religion |
| The place-based alternative | Cuisines can be counted from a source that is already approved. Specialist shops, bookshops and places of worship may be, once its category list has been read. It describes what is there, not who is there. It is still a partial proxy, and must be fenced too |
| Not found today | Any UK case or regulator action about a website showing area demographics. Open data for festivals, language schools or markets |

How this was done, and its limits:

- No web search was made. Every page was reached by opening a known or guessed address. Sources I did not already know of will be missing.
- Pages were read through a reader that summarises. Wording in quotation marks is as that reader returned it, and must be re-checked in a browser before it is relied on.
- One document was read in full as text: the EHRC's 2026 Code of Practice, from the PDF on GOV.UK. Quotations from it are verbatim, with line breaks removed.
- For each census table, the smallest published area was read from the ONS data service's own record of it, not from a description.
- No data file was downloaded or opened.
- Where I report what a company's site shows, I report only the page I opened, with its address and the date. A page that does not mention a thing is not proof the product lacks it.

## Sources

"Read at source" means: **yes**, the publisher's own page stating the licence was fetched today; **part**, only a site footer or a related page was; **no**, the page was not read.

For the census rows, **yes** means the ONS page of at least one table in the row was opened, with the Nomis copyright page. **Part** means only the table's record on the ONS data service was opened, which states no licence. The licence line on an ONS page is the site's footer, and it says "except where otherwise stated".

| Topic | Source | Publisher | Licence as read | Read at source | Smallest area | All of London | Refreshed | Proposed status |
|---|---|---|---|---|---|---|---|---|
| Household type, students | Census 2021 TS003, TS068 | ONS | OGL v3 | Yes | Output area | Yes | Once. Next census 2031 | Gated, display only. Founder decision |
| Age | Census 2021 TS007A | ONS | OGL v3 | Part. The table's own page was not opened | Not confirmed. Output area expected. TS007, age by single year, stops at MSOA | Yes | Once | Gated, display only. Founder decision |
| Country of birth, ethnic group, religion | Census 2021 TS004, TS021, TS030 | ONS | OGL v3 | Yes | Output area | Yes | Once | Held. Founder decision, second step |
| Year of arrival, national identity, passports, household language, English proficiency | Census 2021 TS015, TS027, TS005, TS025, TS029 | ONS | OGL v3 | Part | Output area | Yes | Once | None proposed. Stay in the audit entry |
| Main language | Census 2021 TS024 | ONS | OGL v3 | Part | **Local authority** | By borough only | Once | None proposed. Too coarse |
| Country of birth, detailed | Census 2021 TS012 | ONS | OGL v3 | Part | **Local authority** | By borough only | Once | None proposed. Too coarse |
| Ethnic group and religion, detailed | Census 2021 TS022, TS031 | ONS | OGL v3 | Part | **MSOA** | Yes, but MSOAs do not nest in neighbourhoods | Once | None proposed |
| Sexual orientation, gender identity | Census 2021 TS077, TS078 | ONS | OGL v3 | Yes | **MSOA** | Yes, but see above | Once | None proposed. Never shown, under any option |
| Ethnic group projections | Ethnic group population projections | GLA | Creative Commons Attribution, as the page shows | Yes | **Borough** | By borough only | 2016-based. Last updated about five years ago | None proposed. Too coarse and too old |
| Ward profiles | Ward Profiles and Atlas | GLA | OGL v2 | Yes | Ward | Yes | Compiled September 2015 | None proposed. Too old |
| Area classification | London Output Area Classification 2021 | GLA | OGL v3 | Already `held` | Output area | Yes | Once | Stays held, audit only |
| Cuisines, specialist shops, bookshops, places of worship | Overture Places | Overture Maps Foundation | CDLA-Permissive-2.0 and others | Yes (already `approved`) | Point | Yes. Quality unmeasured | Monthly | Already approved. Category names not confirmed |
| Places to eat, by type of business | Food hygiene ratings | Food Standards Agency | OGL v3 | Yes (already `approved`) | Point | Yes | Daily | Already approved. **It holds no cuisine** |
| Places of worship, by denomination | Places of worship registered for marriage | HM Passport Office | OGL v3, GOV.UK footer | Part | One row per building | Partial by design | Page updated 9 September 2026 | Proposed as `held` in `community.md`. Not repeated here |
| Named places to reach | Wikidata | Wikimedia | CC0 | Yes (already `approved` for destination search) | Point | Coverage unmeasured | Continuous | Already approved |
| Schools with a religious character | Get Information About Schools | DfE | OGL v3 | Yes (already `approved`) | Point | Yes | Daily | Already approved. The field is fenced until the founder decides |
| Theatres, galleries, arts centres, studios | Cultural Infrastructure Map 2023 | GLA | OGL v3, third-party rights unclear | Already `gated` | Point | Yes | Snapshot, 2022 and 2023 | Stays gated on the GLA's reply |
| LGBTQ+ venues | Cultural Infrastructure Map 2024 | GLA | OGL v3, third-party rights unclear | Already `held` | Point | Yes | 2024 | Stays held |
| Festivals, language schools, supplementary schools, markets | None found | | | | | | | None proposed |

## 1. What Census 2021 publishes for small areas

### Tables and the smallest area each is published for

The third column is the `lowest_geography` field of each dataset's own record on the ONS data service, read today.

| Topic the founder named | Table | Smallest area | Counts | Usable at neighbourhood scale |
|---|---|---|---|---|
| Foreign born | TS004 Country of birth, 12 groups | Output area | People | Yes. "Born outside the UK" can be summed exactly |
| Foreign born, by country | TS012 Country of birth, detailed, 60 groups | Local authority | People | **No.** Borough only |
| How recently people arrived | TS015 Year of arrival in the UK | Output area | People | Yes |
| Ethnicities | TS021 Ethnic group, 19 tick-box groups | Output area | People | Yes |
| Ethnicities, detailed | TS022 Ethnic group, detailed, 288 categories | MSOA | People | **No.** MSOAs do not nest in neighbourhoods |
| Language | TS024 Main language, detailed | Local authority | People | **No.** Borough only |
| Language, in the household | TS025 Household language | Output area | Households | Yes, but from memory it says whether English is a main language in the household, not which other language is. The record read today gives only the variable's name |
| English proficiency | TS029 | Output area | People | Yes. It reads as a deficit. I would not show it |
| Religion | TS030, tick-box categories | Output area | People | Yes. The question was voluntary, and "Not answered" is a category |
| Religion, detailed | TS031, 58 categories | MSOA | People | **No** |
| National identity | TS027 | Output area | People | Yes |
| Passports held | TS005, 27 categories | Output area | People | Yes |
| Age | TS007A, five-year bands | Not confirmed today | People | Expected yes. TS007, by single year, stops at MSOA |
| Household type | TS003 Household composition | Output area | Households | Yes |
| Students | TS068 Schoolchildren and full-time students | Output area | People | Yes |
| Sexual orientation | TS077 | MSOA | People aged 16 and over | **No** |
| Gender identity | TS078 | MSOA | People aged 16 and over | **No.** Also downgraded by ONS: see below |

How big these areas are, as ONS states it: an output area has 100 to 625 residents and 40 to 250 households. An MSOA has 5,000 to 15,000 residents. A borough has hundreds of thousands. Burro's plan is about 450 neighbourhoods built from about 26,400 output areas, so about 59 output areas each.

**A figure published for a borough says little about a neighbourhood.** A borough holds about 14 of Burro's neighbourhoods. Pasting the borough's main-language table onto each of them would be one number printed 14 times.

### Licence

| Point | What was read |
|---|---|
| Licence | Each ONS dataset page carries: "All content is available under the Open Government Licence v3.0, except where otherwise stated" |
| Commercial use | OGL v3: "exploit the Information commercially and non-commercially". Nomis: ONS material may be re-used "whether commercially or privately" |
| Attribution | Nomis asks for: "Source: Office for National Statistics" |
| Not covered | OGL v3 does not cover "personal data in the Information" |
| Not allowed | Nomis: "You shall not use products to attempt to obtain or derive information relating specifically to an identified person, household or business" |
| No endorsement | OGL v3 grants no right to suggest "any official status" or that the provider endorses the use |

The licence is not the obstacle. The registry already records this: the census tables are `gated` for a fairness reason, and the entry says "the restriction here is a fairness rule, not a licence limit".

### Disclosure control

ONS changed the data on purpose before publishing it, so that nobody can be picked out.

| Method | What ONS says | What it means for Burro |
|---|---|---|
| Targeted record swapping | "if a household was likely to be identified in datasets because it has unusual characteristics, we swapped the record with a similar one from a nearby small area". The methodology page, as the reader returned it, gives 7 to 10% of households swapped | A household that is unusual for its street may be counted in a nearby small area, which may or may not be in the same neighbourhood. ONS does not publish the effect on any one area |
| Cell key perturbation | "we might change a count of four to a three or a five". As returned: about 14% of cells are changed by a small amount | Each output-area count may be out by a little. Over 59 output areas the noise on a small group adds up. A group of 40 people in a neighbourhood is not a reliable figure |
| Totals differ between tables | "the totals of all cells may in turn be different ... the differences should be small" | Burro's sum for a neighbourhood will not exactly match any ONS total. The page must say so |
| Small counts are published | Zeros, ones and twos may appear where there is "sufficient uncertainty as to whether the small cell count was a true value" | A small count is not a fact about real people. Never print one |

Two quality warnings from ONS bear on what may be shown at all:

- Sexual orientation and gender identity were voluntary questions, and missing answers were not filled in. On 12 September 2024 the gender identity estimates were reclassified as "official statistics in development". ONS says smaller breakdowns "should not be used as precise estimates of the trans population".
- The census counted people where they usually lived on a day in lockdown. ONS's quality report says the pandemic "may have affected some people's choice of usual residence on Census Day", that students are a known case, and that the GLA found "a fall in London's population over the first year of the coronavirus pandemic".

### How stale it will be at launch

| Date | Event | Age of the census figures |
|---|---|---|
| 21 March 2021 | Census Day | |
| 28 June 2022 | First results published | |
| Late January 2027 | Planned web launch | 5 years, 10 months |
| March 2027 | Planned iOS approval | 6 years |
| 2031 | Next census. ONS says the government confirmed in July 2025 that it was commissioning one | 10 years |
| About 2032 to 2033 | Small-area results of the next census, if the last timetable repeats. **My inference, not an ONS statement** | 11 years or more, until replaced |

I found no newer small-area source. The GLA's ethnic group projections are for boroughs and start from 2016. ONS's yearly small-area population estimates hold age and sex only, and the registry already drops those columns.

London changes faster than most places. A figure about who lived in a fast-changing neighbourhood in March 2021 may be wrong about who lives there in 2027, and nothing in the data says where.

## 2. What comparable UK services show

Every row is a page I opened on 2026-09-23, through a reader that summarises. I make no claim about any product beyond the page named.

| Service | Page opened | What the page shows about residents | How it presents it |
|---|---|---|---|
| ONS data service | `ons.gov.uk/datasets/TS021/...`, and the API records | Ethnic group, religion, country of birth and more, down to output area | Tables to download. The state's own publication |
| ONS Census maps | `ons.gov.uk/census/maps` | Not read | |
| Nomis | `nomisweb.co.uk/reports/localarea` | Official census reports for areas "down to output areas", as returned | Reports by area |
| GLA Ward Profiles and Atlas | `data.london.gov.uk/dataset/ward-profiles-and-atlas` | "household composition, religion, ethnicity" among many indicators, by ward | A profile per ward. Compiled September 2015 |
| Crystal Roof | `crystalroof.co.uk/` and `/report/postcode/<postcode>/demographics` | Home page lists "Ethnic group, Religion, Household type, Residents age", and under affluence "Income of the local households, Deprivation level, Social grades of the local residents, Qualification levels". The report page has sections "Ethnic Makeup", "Religion", "Residents Age", "Household Type" | Each section opens with a label: "Main ethnicity", "Main religion", "Main age band", "Main household type". Categories carry "Higher than average" or "Lower than average". Source line: Office for National Statistics, Census 2021. The overview page showed two items behind an upgrade. No filter by residents was on the pages read |
| StreetCheck | `streetcheck.co.uk/postcode/<postcode>` | The address led to the Crystal Roof report for the same postcode | |
| postcodearea.co.uk | `postcodearea.co.uk/postaltowns/london/e8/` | Sections include "People and Demographics", "Ethnicity", "Health", with country of birth, length of residence, gender identity and more. Source given as Census 2021 | Tables and charts by postcode district |
| Know Your Area | `knowyourarea.co.uk/` | "We also hold age demographics and population density data, allowing you to find areas for your preferred age bracket and family values." | The wording describes finding areas by age. No mention of ethnicity, religion or income on the page |
| Doogal | `doogal.co.uk/ShowMap?postcode=<postcode>` | Population and household counts from the 2011 census, and an average household income. No ethnicity, religion or age | A postcode fact sheet |
| GetTheData | `getthedata.com/postcode/<postcode>` | No resident demographics. A deprivation section | A postcode fact sheet |
| PropertyData | `propertydata.co.uk/` | Tenure and property type from the census. No feature named demographics on the page | |
| Mappa | `usemappa.com/` | No mention of resident demographics on the page. Ranks "based on your lifestyle and personal needs" | |
| Agentor | `agentor.co.uk/` | No mention on the page. Twelve metrics, all of places | |
| Neighbourhood Finder | `neighbourhoodfinder.co.uk/` | No mention on the page | |
| Chimnie | `chimnie.co.uk/` | No mention on the page | |
| Zoopla, Rightmove, OnTheMarket | Home pages | No mention on any of the three home pages. No area guide was read | |
| Locrating, Home.co.uk | Home pages | Not read | |
| iLiveHere | A statistics page | Not read | |
| Urbanity | Home page | Not read | |

What the pattern is, on these pages only:

| Pattern | Seen |
|---|---|
| Official bodies publish resident statistics for very small areas, openly | ONS, Nomis, GLA |
| Some commercial sites reprint them by postcode or postcode district | Two of those read |
| A site labels the largest group in an area | One of those two |
| A site says users can find areas by residents' age | One |
| A site offers a filter or a ranking by ethnicity or religion | None of those read |
| Area finders that rank or match say nothing of residents on their home pages | Four of four |

From outside Britain, and under different law: Redfin's post of 13 December 2021 says it would not show neighbourhood crime data, citing "the long history of redlining and racist housing covenants in the United States" and "too great a risk of this inaccuracy reinforcing racial bias". ADR 0006 already cites this.

## 3. The law and guidance, as far as public sources go

I am not a lawyer. This section reports what public documents say and how I read them. It does not say what a court would decide. No professional has reviewed it.

### What was read

| Source | The words | What it means for Burro, on my reading |
|---|---|---|
| Equality Act 2010, section 4 | The protected characteristics: "age; disability; gender reassignment; marriage and civil partnership; pregnancy and maternity; race; religion or belief; sex; sexual orientation" | Almost every census table about residents touches one |
| Section 9 | "Race includes (a) colour; (b) nationality; (c) ethnic or national origins" | Country of birth and national identity are race, for the Act |
| Section 29(1) | "A person (a 'service-provider') concerned with the provision of a service to the public or a section of the public (for payment or not) must not discriminate against a person requiring the service" | Burro is a service provider, free or paid. The duty runs to the person using Burro |
| Section 28 | Part 3 does not apply to age under 18, or to marriage and civil partnership | Household composition is not itself protected in services. Age is, for adults |
| Section 13(1) | "A person (A) discriminates against another (B) if, because of a protected characteristic, A treats B less favourably than A treats or would treat others" | The test is how Burro treats its users. It need not be the user's own characteristic |
| Section 13(5) | "If the protected characteristic is race, less favourable treatment includes segregating B from others" | For race, segregation needs no comparison |
| Section 19 | A "provision, criterion or practice" that puts people sharing a characteristic "at a particular disadvantage", unless it is "a proportionate means of achieving a legitimate aim" | A neutral rule can discriminate. This is why the proxy audit exists |
| Section 26 | Harassment: "unwanted conduct related to a relevant protected characteristic" with "the purpose or effect of" violating dignity or creating "an intimidating, hostile, degrading, humiliating or offensive environment" | Wording about a group can be conduct. Intent is not needed |
| Sections 32, 33, 38 | Section 33 binds "a person (A) who has the right to dispose of premises". The Code, para 11.66, says Part 4 "covers, for example, those who provide premises for rent and those who manage rented properties" | Burro disposes of no premises, manages none and has no listings. On my reading Part 4 is not engaged today. It would need re-reading if Burro ever carried listings or took money from agents |
| Section 111 | A person must not instruct, cause or induce another to do, to a third person, anything that contravenes the Act. It applies only where the relationship between the two is one the Act covers. The EHRC may bring proceedings itself | It would matter if Burro ever worked with agents or landlords. A person choosing where to live contravenes nothing |
| Section 119 | The county court may award damages, including "compensation for injured feelings" | Claims are brought by individuals in the county court |
| Equality Act 2006, section 20 | The EHRC may investigate where "it suspects that the person concerned may have committed an unlawful act" | The regulator has its own powers |
| EHRC Code of Practice 2026, para 1.6 | "The Code does not impose legal obligations. Nor is it an authoritative statement of the law ... Courts and tribunals must consider any part of the Code that appears relevant" | It is the best public guide there is. In force from 5 August 2026 |
| Code, para 3.6 | "The obligation also applies to the provision of services on a website (section 29)" | |
| Code, para 11.74 | "Some goods and services are provided remotely through mediums like websites or apps, for example, where they are delivering information, products or entertainment to the public" | An information service in an app is a service |
| Code, para 11.58 | "Part 4 applies where an estate agent is letting or managing property on behalf of an owner, but not where an estate agent is advertising or providing information about properties. Instead, the latter activities would constitute services to the public" | **This settles a point the earlier research did not reach.** Information about where to live is a Part 3 service |
| Code, para 4.11 | "When the protected characteristic is race, deliberately segregating an individual or group of individuals from others of a different race automatically amounts to less favourable treatment ... The segregation must be a deliberate act or policy rather than a situation that has occurred inadvertently" | The line is between what the provider does and what happens |
| Code, para 4.13 | At a youth club open to all, boys who "choose to separate themselves": "Because this is a choice of the users of the youth club, and not an enforced policy of the club, it would not amount to segregation and would not be unlawful" | A user who reads a figure and chooses for themselves is the user's choice. A tool that sorts for them is nearer to the provider's act |
| Code, para 4.27 | "Direct discrimination also includes less favourable treatment of a person based on a stereotype relating to a protected characteristic, whether or not the stereotype is accurate for that person" | A vibe built on who lives somewhere is a stereotype written as arithmetic |
| Code, para 5.62 | An algorithm flags a postcode for extra checks. "The area has a large population of residents of Bangladeshi heritage who are put at a disadvantage by the additional, postcode-specific fraud detection checks ... Unless the local authority can justify the policy, they may have a claim for indirect discrimination" | The EHRC's own example of an area standing in for race |
| Code, para 8.6 | Harassment in services "does not protect individuals who have the protected characteristics of sexual orientation or religion or belief", though a detriment may be direct discrimination | Race is covered by harassment. Religion is reached another way |
| Code, para 8.16 | "The intended purpose or motive behind the conduct is irrelevant" | A well-meant label can still offend |
| ICO, special category data | Special categories include "personal data revealing racial or ethnic origin" and "religious or philosophical beliefs". Inferred data counts if "your processing intends to make an inference linked to one of the special categories" or "you intend to treat someone differently on the basis of inferred information". "If you carry out any form of profiling which infers things like ethnicity, beliefs ... you will be processing special category data" | This is about the person searching, not the area. It bites when a search reveals who the searcher is |
| ICO, anonymisation | "Data protection law does not apply to anonymous information" | Census tables are statistics, already disclosure-controlled. Showing them is not processing personal data |
| ICO, fairness in AI | "simply removing special category data (or protected characteristics) does not guarantee that other proxy variables cannot essentially reproduce previous patterns". On equality law: "Compliance with one will not guarantee compliance with the other" | Removing the census does not remove the proxy. The audit is still needed |
| ASA, what it covers | "Claims made on a company's website or app". Not "Editorial content" | Burro's own marketing copy is in scope. Whether a statistics panel is marketing or editorial is not clear to me |
| CAP Code, rule 4.1 | "Marketing communications must not contain anything that is likely to cause serious or widespread offence. Particular care must be taken to avoid causing offence on the grounds of: age; disability ... race; religion or belief; sex; and sexual orientation" | A vibe label tied to a group, used in an advert, is exposed here |
| CAP Code, rules 3.1 and 3.7 | "Marketing communications must not materially mislead". Marketers "must hold documentary evidence to prove claims that consumers are likely to regard as objective" | A six-year-old figure presented as today's could mislead |
| ASA advice on race, 23 February 2026 | "The inclusion of negative racial stereotypes is likely to cause serious and widespread offence." As the reader returned it, the advice also records a ruling against a stereotype that was meant as praise | A flattering label about a group is not safe either |

### Show, rank, vibe: three different acts

| | SHOW a statistic on an area page | RANK or FILTER areas by who lives there | Build a named VIBE partly from who lives there |
|---|---|---|---|
| What Burro does | Prints the official figure, the same for every visitor | Changes which areas a person sees, or their order, by residents' characteristics | Gives an area a label by Burro's own recipe. The label is shown, and can be ranked on |
| Who acts on race or religion | The reader, if anyone | Burro's code, when a user asks | Burro's code, for every user, asked or not |
| Licence | Allowed | Allowed | Allowed |
| Data protection | Statistics, not personal data | The filter a person sets can reveal their own faith or origin. It travels in the spec, and sits in any share link made from it | As for show. If the vibe is also a filter, as for rank |
| Equality Act, where it could bite | Wording. A label or a comparison that reads as a judgement on a group could be harassment related to race, or a detriment. A plain table is far from that | Segregation, if a court saw the filter as Burro's deliberate policy and not the user's choice. Indirect discrimination, if a ranking rule disadvantages users who share a characteristic. No public source I read decides either | All of rank, because a tag is rankable. And stereotype: the label says what a group's presence means |
| ASA | Staleness, if the figure is used in marketing | Copy such as "find people like you" | Any advert that uses the label |
| Practice seen today | The state does it. Two commercial sites read today do it | One site's wording describes finding areas by age. None by ethnicity or religion | None |
| UK regulator action found | None | None. The Code's postcode example and the FCA's study show the pattern is watched | None |
| What stays true whatever a lawyer says | The figure is old, and was taken in lockdown | Burro's public sentence, "never by who lives there", would have to go | Burro shows its working. The working would read: this area is "gritty" partly because of who lives there |
| My reading of the risk | The lowest of the three. Real, and mostly about presentation | High, and unreviewed | The highest |

### UK cases and regulator action found

| What | Who | Date | What it shows |
|---|---|---|---|
| Research note, "Motor insurance pricing and local area ethnicity in England and Wales" | Financial Conduct Authority | 10 December 2025 | The FCA studied 6 million policies after Citizens Advice reported that people in areas with more minority ethnic residents paid more. It found the gap "overwhelmingly explained by the differences in risk between different areas", with a smaller part unexplained. No enforcement followed, on what I read. **A UK regulator examined whether an area-based rule stood in for ethnicity** |
| Code of Practice example 5.62 | EHRC | In force 5 August 2026 | The statutory Code teaches indirect race discrimination with a postcode example |
| A UK case or regulator action about a website showing area demographics | | | **None found.** That is a limit of the search as much as a finding |

Three leads I know of from memory and did not verify today. Nothing in this report relies on them:

- Formal investigations of estate agents for racial steering by the former Commission for Racial Equality, in the 1980s and 1990s.
- County court rulings from 2020 that letting agents' blanket bans on tenants receiving benefits were indirect discrimination.
- The Citizens Advice report that the FCA's study answered.

### What the law reading does not settle

| Open point | Why it matters |
|---|---|
| Whether a filter by residents that a user chooses to apply is the provider's "deliberate act or policy" | It decides whether rank and filter can ever be offered. Only a court or a lawyer can say |
| Whether a plain statistics panel could be "unwanted conduct related to" race | It decides how careful the panel's wording must be. I think a verbatim table is far from it. I cannot promise it |
| Whether a resident of an area, who is not a Burro user, has any claim | The duties in section 29 run to users. I found nothing that gives a non-user a route. I did not look for every route |
| Apple's review rules | Not re-read today. The earlier research names guideline 1.1.1 |

## 4. Describing cultural background through places

ADR 0006 already says a wish for community is met "through amenities: places of worship, specialist shops, venues". Today no feature does it, and such a request is reported as unmet. This is what could fill the gap.

### What each kind of place can carry

| Kind of place | Source | What was confirmed today | What was not |
|---|---|---|---|
| Restaurants and cafes, by cuisine | Overture Places | The taxonomy has about 2,300 categories and names cuisines. The guide gives "sushi_restaurant" and "cantonese_restaurant" as examples | The full list. It is loaded by script. London quality is unmeasured |
| Restaurants and cafes, by cuisine | Food hygiene ratings | **It cannot do this.** The 14 business types are broad: "Restaurant/Cafe/Canteen", "Takeaway/sandwich shop", "Retailers - other" and so on. There is no cuisine field | |
| Specialist grocers and food shops | Overture Places | Nothing | Whether the taxonomy names them |
| Bookshops | Overture Places | Nothing | Whether the taxonomy names them |
| Places of worship | Overture Places, the marriage list, Wikidata | The marriage list leaves out every Anglican church and every building not registered for marriages. See `community.md` | Overture's categories by faith. Whether OS OpenMap Local marks them |
| Cultural and community centres, theatres, galleries | GLA Cultural Infrastructure Map, Overture | The GLA layers are `gated` or `held` on third-party rights. Features are proposed in `culture.md` and `community.md`, and are not repeated here | The GLA's reply |
| Schools with a religious character | Get Information About Schools | The source is approved. The field is fenced "until the founder decides" | |
| Language schools, supplementary schools | None found | | Whether any register exists under an open licence |
| Festivals and regular cultural events | None found | | |
| Markets | None found | The London Datastore page was not read | |

### What it captures, and what it misses

| It captures | It misses |
|---|---|
| What a person can eat, buy, attend and join within a walk | Who the neighbours are |
| The visible character of a high street | Communities that meet in homes, or have no building of their own |
| Things useful to anyone, whatever their own background | The language at the school gate |
| Change, month by month, because the sources refresh | Age, household type and how long people stay |
| | Places lag people. A church outlasts its congregation. A new community has no venue yet |
| | A cuisine says little about residents. Restaurants follow customers, and customers travel |

### Is it itself a proxy?

Yes, in part. A count of mosques or kosher shops in an area goes with the share of residents of that faith. The ICO's guidance says exactly this of proxy variables. The difference from the census is one of degree and of use, not of kind. So the fence has to be built here too.

| Safeguard | Why |
|---|---|
| One direction only. A person may ask to be near. Never far, never fewer | "Far from a mosque" is a request about people. ADR 0006 already refuses it for campuses |
| On request only. A community's amenity carries no default weight and sits in no tag | It answers a need the person stated. It never shapes anyone else's ranking |
| Never turned into a label for the area | "A Turkish area" is a claim about residents, whatever it was counted from |
| Variety, not share. Count how many cuisines, not which one leads | A count of kinds describes a high street. A leading cuisine describes a community |
| In the proxy audit, with a written rule, before it ranks | The plan already requires this of every feature |
| The best form is a destination | A person names the place they need to reach, as they name a workplace. Burro routes to it. No area is scored by faith, and no area is labelled |

The last row uses what Burro already has. A person may name up to three places they must reach. If one is a place of worship, a community centre or a language school, the commute machinery serves it as it serves an office. The privacy rule already covers it: a destination is never logged, and a share coarsens it to a station or district. What it needs is that the place index can find such places by name.

## What could be built

### From places. Needed under every option

| Proposed | Label | Describes | From | Resolution | Buildable |
|---|---|---|---|---|---|
| A community place as a destination | A place I need to reach | **Place** | `wikidata-places-and-landmarks`, `dfe-gias`. Both approved for destination search | Point. Journey time from each area | After a coverage check: can the index find the 50 best-known places of worship and community centres in London by name |
| `cuisine_variety` | Kinds of cuisine among places to eat within a 15-minute walk | **Place** | `overture-places` | Point, network walk | After the London quality spike, and once the category list has been read |
| `specialist_food_shops` | Specialist food shops within a 15-minute walk | **Place** | `overture-places` | Point, network walk | Only if the taxonomy names them. Not confirmed |
| `bookshop_nearby` | Bookshops within a 15-minute walk | **Place** | `overture-places` | Point, network walk | Only if the taxonomy names them. Not confirmed |
| `worship_proximity` | A place of worship within a walk, no faith named | **Place** | See `community.md`, decision 1 | Point | Founder decision first |
| A community's amenity, by kind, on request | Near a named kind of place | **Place** | A source that covers faiths and communities evenly. None confirmed | Point | Held. See `community.md`, choice C |
| A school's religious character | Shown on the school's own line | **Place**, a school | `dfe-gias` | Point | Founder decision |
| Tag, working name "World food" | Many cuisines, many independents | **Place** | `cuisine_variety` high, `venue_independent` high | Tag | After the proxy audit and the 40-neighbourhood sanity set |

On the area page these make a section, "Culture and community", of places only. A fixed line closes it: "Burro counts places. It does not describe the people who live here."

### From the census. Only if the founder chooses Option 2

Every row below describes **residents**. Each is for display on the area page only.

| Proposed | Shows | Describes | From | Resolution | Step |
|---|---|---|---|---|---|
| Age bands | Share of residents in each band | **Residents** | TS007A | Output areas, summed to the neighbourhood. To be confirmed | First |
| Household type | Share of households of each type | **Residents** | TS003 | Output areas, summed | First |
| Students | Share who are full-time students | **Residents** | TS068 | Output areas, summed | First |
| Born in the UK or outside it | Two shares, and the 12 broad groups | **Residents** | TS004 | Output areas, summed | Second |
| Ethnic group | ONS's categories, in ONS's words and order | **Residents** | TS021 | Output areas, summed | Second |
| Religion | ONS's categories, with "Not answered" | **Residents** | TS030 | Output areas, summed | Second |

How the panel would work, so that showing never becomes ranking:

| Rule | Detail |
|---|---|
| Where | The area page only. Its own section, headed "Census 2021: who lived here". The past tense is deliberate |
| Second-step tables | Closed by default. The person opens them |
| Form | A table: ONS's category, share as a whole percent, and the London share as a plain number beside it |
| No labels | No "main ethnicity". No "higher than average". No colour scale. No adjective |
| Small groups | A category under 1% of the neighbourhood is shown as "under 1%". No count is printed |
| Source line | "Source: Office for National Statistics, Census 2021. Census Day was 21 March 2021, during a national lockdown. Figures are sums for the small areas that make up this neighbourhood. ONS adjusts small counts to protect privacy, so totals may differ slightly from its own." |
| Fixed sentence | "Burro never uses these figures to rank, filter or describe a place." |
| Never in | Results, reasons, trade-offs, tags, sliders, filters, sorting, the map, comparison, shares, the prompt reader's vocabulary, or anything a model is sent |
| A request about residents | Still gets the neutral sentence, and still makes no edit. The sentence may add where the census figures can be found |
| Sentences | None. The verifier cannot yet catch a claim about residents (contract 7.4). Resident figures are a table, never a sentence |

## What cannot be done honestly

| Claim or feature | Why not |
|---|---|
| "Polish is widely spoken here", or any language by neighbourhood | Main language is published for boroughs only |
| "Many residents were born in Turkey", or any country by neighbourhood | Detailed country of birth is published for boroughs only. Output areas hold 12 broad groups |
| Detailed ethnic group or detailed religion by neighbourhood | Published for MSOAs, which do not nest in Burro's neighbourhoods. Splitting them would be a model, not a fact |
| Sexual orientation or gender identity by neighbourhood | MSOA only. Voluntary questions. ONS has downgraded the gender identity estimates and warns against precise use for small groups |
| "Who lives here", in the present tense | The census is 5 years and 10 months old at launch, and was taken in lockdown |
| A small group's share, to the percent | Perturbation noise adds up over 59 output areas |
| A borough figure shown as a neighbourhood's | It would be the same number on about 14 pages |
| A label for an area's community: "a Turkish area", "a Jewish area" | From residents it is a stereotype. From venues it is a proxy, on a source whose London quality is unmeasured |
| "Diverse", "cosmopolitan", "multicultural" as a tag | Each is a judgement about residents. A variety of cuisines is a fact about restaurants, and should be named as that |
| "Gritty", where any input describes residents | Income, employment, health and ethnicity describe people. A named vibe built on them says what those people make a place |
| Cuisine from the food hygiene register | It has no cuisine field |
| A count of places of worship by faith, from the marriage list | It omits Anglican churches and unregistered buildings, unevenly by faith. See `community.md` |
| Festivals, language schools, supplementary schools, markets | No open source was found |
| Inferring residents from places, or places from residents | Either way it is a guess shown as a fact |
| A sentence about residents written by a model | The verifier passes "popular with young families" today. The contract says so |
| Any update between censuses | No newer small-area source was found |

## What the founder must decide

The rules as they stand say no resident data reaches a user. ADR 0006 was adopted because there is no money for legal advice. Until the founder decides otherwise, that is what the code enforces, and nothing in this report changes it.

### The three options

| | Option 1. Places only | Option 2. Show, never rank | Option 3. Residents in ranking or vibes |
|---|---|---|---|
| In one line | ADR 0006 as written. Culture comes from places | Census figures on the area page, in a fenced panel. Everything else as Option 1 | Resident data feeds a tag, a filter or a weight |
| What a person can do | Ask for cuisines, shops, venues. Name a place of worship as a destination. Read "Culture and community" on the area page | All of Option 1. And read who lived in the area in 2021, from the official figures | All of Option 2. And search or sort by who lives there, or by a vibe built from it |
| What it gives the founder's item 8 | "Cultural background and vibe": yes, from places. "Local makeup, foreign born, ethnicities": no | Both | Both, and as a search |
| Optional add-on | A plain link from the area page to the ONS's own census pages. Burro shows and stores nothing | | |
| What must change | Nothing in the rules. New features need registry and catalogue changes as usual | ADR 0006, plan section 15, the registry's rule on audit data, the audit entry's conditions, and a new fence in code. Listed below | All of Option 2. And AGENTS.md rule 8, the neutral sentence, and the public fairness position |
| Legal exposure, on my reading | The least. Proxy effects remain, and the audit covers them | Low, and mostly in the wording. Not zero, and unreviewed | High. Segregation, indirect discrimination and stereotype are all in play, and unreviewed |
| Data protection | None new | None new, if the panel is never a filter | A person's filter reveals their own faith or origin. Special category data, in the spec and in shares |
| Reputation | Consistent with "never by who lives there" | Defensible: "we show the official figures, and never rank on them". A critic can still say a finder that prints ethnicity invites steering | The hardest of the three to defend in public |
| Truth | Place data is fresh. Its London quality is unmeasured | The census is old. The panel must say so every time | The ranking would rest on six-year-old figures |
| Safeguards it needs | One direction. On request only. No area labels. Proxy audit | The panel rules above. A code fence, with a test. The panel's words read by someone qualified, or the risk accepted in writing | Paid legal advice first. ADR 0007 rules this out today |

### What I recommend, and why

**Option 2, in two steps. Never Option 3 without paid advice. And the vibe comes from places.**

| Step | What | When | Gate |
|---|---|---|---|
| 0 | Build the place-based features: a community place as a destination, `cuisine_variety`, the "Culture and community" section | Now. Every option needs them | The usual: registry, catalogue, proxy audit row |
| 1 | The census panel with age bands, household type and students | At launch | The founder amends ADR 0006. The code fence and its test exist |
| 2 | Add country of birth, ethnic group and religion to the panel, closed by default | When the gate passes. It can pass before launch | Either a free legal clinic or a fixed-fee adviser has read the panel and this section. Or the founder writes in ADR 0006 that the leftover risk is accepted, with the date |
| Until step 2 | A plain link from the area page to the ONS's census pages | At launch | None |

Why this, and not the others:

1. **The founder has said the local makeup is part of the product.** The plan's own test, in ADR 0007, is "the most conservative design that still delivers the product". If the makeup is part of the product, Option 1 does not deliver it and Option 3 is not the most conservative. A fenced panel is.
2. **Showing is where the evidence is least worrying.** The state publishes these figures for areas of 100 people. Sites reprint them. The Code's test for segregation turns on the provider's "deliberate act or policy", and its youth club example treats the users' own choice as lawful. I found no UK action against display. None of that is clearance. It is the reason showing sits apart from the other two.
3. **Ranking and vibes are where Burro itself would act on race or religion.** No public source I read says that is lawful, and the Code's postcode example shows how it would be analysed. Burro also shows its working. A vibe built on who lives somewhere would show that working to every user and every journalist.
4. **The two steps follow the risk.** Race and religion are where the segregation rule, harassment, special category data and the ASA's advice all sit. Age and household type carry much less of each. Step 1 can ship without waiting. Step 2 waits only for a reading, or for the founder's signature.
5. **Places answer most of what was asked.** Six of the founder's eight items are about places. Items 2 and 8 are partly about people, and each has a part that places can answer. A high street's cuisines, shops and venues say more about what living there is like today than a 2021 table does.

Where this departs from what is already written: the plan, in section 15, says Burro will not show "ethnicity, religion or age breakdowns", even for information. Two earlier reports, `liveability-demographics` and `accounts-compliance`, rejected showing ethnicity and religion, and one of them judged the product value small. The founder has now said otherwise, and today's reading of the Code is the first that reached its whole text. If the founder prefers the position as written, Option 1 with the link to ONS is the safest way to still answer the question.

### Smaller decisions

| # | Decision | Recommendation |
|---|---|---|
| 1 | May a place of worship, a community centre or a language school be named as a destination? | Yes. It is a place a person must reach. It needs a coverage check of the place index, and nothing else |
| 2 | Link from the area page to the ONS's census pages? | Yes, under Option 1 and until step 2 under Option 2. Check first that the ONS pages can be linked by area |
| 3 | Apply to a free legal clinic now? | Yes. Send this section, the panel rules and one question: may a consumer service print ONS census tables about residents on an area page, if it never ranks or filters on them. Set a date after which the founder decides without a reply |
| 4 | May a cuisine list be shown on the area page, or only the count of kinds? | The count, and an alphabetical list of the cuisines present. Never ordered by how many |
| 5 | Should the second-step tables be closed by default? | Yes. It makes reading them a choice, keeps them off the first screen and out of link previews |
| 6 | May the census panel appear in comparison? | No, at first. Side by side it becomes a way to choose between areas by residents |
| 7 | "Gritty", the founder's item 2: may any input that describes residents feed it? | No, under every option. Build it from places: recorded crime is already fenced out of tags, so a decision is needed there too. That belongs to the report on that vibe |
| 8 | Tenure on the area page: private rent only, or all three shares? | Private rent only. If Option 2 is chosen, the panel is the place for the other two, under the same rules |
| 9 | English proficiency, year of arrival, passports, national identity | Do not show. Each adds little to the three second-step tables and reads as a judgement |
| 10 | Sexual orientation and gender identity | Never shown, under any option. Too coarse, and ONS warns against it |

### What would have to change in the repository under Option 2

I have changed none of these. They are for the founder and the owners of each part.

| Where | Change |
|---|---|
| `docs/adr/0006` | Amend: resident statistics may be shown on the area page under the panel rules. They still never feed ranking, a tag, a filter or a sentence |
| `docs/PLAN.md`, section 15 | The line that Burro will not show "ethnicity, religion or age breakdowns" is no longer true as written. Decision 4 in section 14 changes with it |
| `AGENTS.md`, rule 8 | Its first two sentences stand: Option 2 keeps residents out of ranking and tags. Its third says protected-characteristic data is registered as `audit_only`, and would need rewording |
| `registry/README.md` | The rule "protected-characteristic tables must never reach a user" needs rewording |
| `registry/sources/audit.toml` | The audit entry lists the same tables and forbids "any page". It must be reworded in the same change, or the registry says two things at once |
| Registry code | A new dimension, `residents`. A new rule: a source in it may have the use `display` and internal uses, and no other. Today nothing stops a census table being registered for `scoring` under another dimension |
| Release format | A file of its own for resident figures, asked of the registry as `display`. `rank()`, tags and `explain()` never open it |
| Tests | No feature, tag or sentence cites a source in the `residents` dimension. The panel's text is fixed and rendered by a test |
| Contract, section 8.4 | The neutral sentence may point to the panel. No edit is ever made from a request about residents |

## What was not read

| What | Standing | Relied on instead |
|---|---|---|
| Web search | None was made | Known or guessed addresses |
| Raw page text | Pages were read through a reader that summarises | The reader's output, marked as such. One PDF was read in full as text |
| EHRC website | Not read | The Code of Practice as published on GOV.UK |
| The Code's HTML page | Read as far as paragraph 4.72 | The PDF, read in full |
| Nomis table list by area, and the Nomis API | Not read | The ONS data service's record for each table |
| TS007A on the ONS data service | Not read | Nothing. Its smallest area is unconfirmed |
| ONS Census maps, and "Build a custom area profile" | Not read | The dataset records |
| Citizens Advice, the insurance report | Not read | The FCA's account of it |
| Shelter, the 2020 rulings | Not read | Nothing. No claim is made |
| Commission for Racial Equality investigations of estate agents | Not searched for. No address known | Nothing. No claim is made |
| Zoopla and Rightmove area guides | Not read | Their home pages |
| Locrating, Home.co.uk | Not read | Nothing |
| iLiveHere | Not read | Nothing |
| Urbanity | Not read | Nothing |
| Crystal Roof's terms | Not read | Nothing. No claim is made about its terms |
| Overture's list of categories | Not read | The guide, which names two cuisine categories |
| OS OpenMap Local code list | Not read | Nothing |
| Charity Commission register | Not read | Nothing. See `community.md` |
| London Datastore, markets | Not read | Nothing |
| Apple's App Store review guidelines | Not re-read | The earlier research |

## Unverified

- The smallest area for TS007A, age in five-year bands.
- The shares the ONS methodology page gives for swapped households and perturbed cells. They are as the reader returned them.
- That the next census's small-area results will arrive in 2032 or 2033. My inference from the last timetable.
- That Overture's taxonomy names places of worship by faith, specialist grocers and bookshops.
- That the ONS census pages can be linked to by area code.
- That a plain statistics panel is outside harassment under the Act. My reading. No lawyer has seen it.
- That no UK action has been taken against a site for showing area demographics. I found none. No search was made.
- Every statement about what a company's product does beyond the page named.
- The three leads listed under "UK cases and regulator action found".
- How the marriage list's omissions fall across faiths.

## Proposed registry entries

For review. Not added to the registry.

**Neither entry validates against today's registry, and that is deliberate.** There is no `residents` dimension, and the registry's rules keep protected-characteristic tables from any user. The entries are written out so the founder can see exactly what Option 2 would add. Under Option 1 neither is added.

The licence would support `approved`: the publisher's pages were opened today and plainly allow commercial use. The status is `gated` and `held` because the gate is a fairness decision, not a licence check.

This report proposes no entry for a place-based source. Overture Places, the food hygiene register, Wikidata and Get Information About Schools are already registered. The marriage list and the Charity Commission register are proposed in `community.md`, and an id appears once.

```toml
# Proposed by docs/research/vibes/people.md on 2026-09-23.
# Would go in a new file, registry/sources/residents.toml.
# Needs a new Dimension member, "residents", and a new rule:
#   a source in this dimension may have the use "display" and internal uses, and no other.
# Needs the audit entry ons-census-2021-protected-characteristics reworded in the same change:
#   it lists TS007A, TS004, TS021 and TS030 and forbids any page.

[[source]]
id = "ons-census-2021-life-stage-tables"
name = "Census 2021 tables on age and households, for display only: TS003 household composition, TS007A age by five-year bands, TS068 schoolchildren and full-time students"
publisher = "Office for National Statistics"
url = "https://www.ons.gov.uk/datasets/TS003/editions/2021/versions/3"
dimension = "residents"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "Source: Office for National Statistics"
attribution_verified = false
conditions = [
    "Display on the area page only, in the census panel, under the rules in docs/research/vibes/people.md.",
    "Never an input to ranking, a tag, a filter, a sort, a map layer, a comparison, a share, an explanation, or anything sent to a model (ADR 0006).",
    "These tables describe residents. Age is a protected characteristic.",
    "Shown as a table, never as a sentence. No label for the largest group. No 'higher than average'. No colour scale.",
    "Figures are sums of output-area estimates. A category under 1% of a neighbourhood is shown as 'under 1%'. No count is printed.",
    "State on every panel: Census Day was 21 March 2021, during a national lockdown. ONS adjusts small counts to protect privacy, so totals may differ slightly from its own.",
    "Kept in a release file of its own, asked of the registry as 'display'. rank(), tags and explain() never open it. A test proves it.",
    "Nomis terms: do not use the data to attempt to obtain or derive information about an identified person, household or business.",
    "Link to the Open Government Licence beside the source line. Do not suggest ONS endorses Burro.",
]
status = "gated"
status_reason = "The licence is confirmed. It is gated on a founder decision, not on a licence check. Gate: (1) the founder amends ADR 0006 and PLAN section 15 to allow resident statistics on the area page; (2) the registry gains the 'residents' dimension and the display-only rule; (3) the release format has a separate file for resident figures and a test that no feature, tag or sentence cites it; (4) the smallest area for TS007A is confirmed as output area."
uses = ["display"]
cadence = "One-off. Census Day 21 March 2021. Next census 2031."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.ons.gov.uk/datasets/TS003/editions/2021/versions/3",
    "https://api.beta.ons.gov.uk/v1/datasets/TS003/editions/2021/versions/3",
    "https://api.beta.ons.gov.uk/v1/datasets/TS068/editions/2021/versions/3",
    "https://www.nomisweb.co.uk/home/copyright.asp",
    "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
    "https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/methodologies/protectingpersonaldataincensus2021results",
]
notes = "How it was verified: the ONS dataset page for TS003 states 'All content is available under the Open Government Licence v3.0, except where otherwise stated', and the Nomis copyright page allows re-use 'whether commercially or privately'. The ONS data service records lowest_geography 'oa' for TS003 and TS068. TS007A was not read on the data service, so its smallest area is unconfirmed; TS007, age by single year, is recorded as 'msoa'. TS003 counts households, not people. All pages were read through a reader that summarises: re-check in a browser when saving evidence. Tenure, TS054, already has its own entry under housing."

[[source]]
id = "ons-census-2021-origin-and-belief-tables"
name = "Census 2021 tables on country of birth, ethnic group and religion, for display only: TS004, TS021, TS030"
publisher = "Office for National Statistics"
url = "https://www.ons.gov.uk/datasets/TS021/editions/2021/versions/3"
dimension = "residents"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "Source: Office for National Statistics"
attribution_verified = false
conditions = [
    "Every condition of ons-census-2021-life-stage-tables applies.",
    "Closed by default on the area page. The person opens it.",
    "ONS's categories, in ONS's words and ONS's order. Never regrouped, renamed or ranked by size.",
    "Religion was a voluntary question. 'Not answered' is always shown.",
    "Race and religion are protected characteristics. Country of birth is race, for the Equality Act: section 9 includes national origins.",
    "The detailed tables are not covered and must not be shown for a neighbourhood: TS012 and TS024 are published for local authorities only, TS022 and TS031 for MSOAs only.",
    "Sexual orientation and gender identity, TS077 and TS078, are not covered and are never shown.",
]
status = "held"
status_reason = "Held on a founder decision and on a reading, not on licence. Released by either (1) a free legal clinic or a fixed-fee adviser having read the census panel and section 3 of docs/research/vibes/people.md, with a dated note of the reply in registry/evidence/, or (2) the founder recording in ADR 0006 that the leftover risk is accepted, with the date. Then it becomes gated on the same gate as ons-census-2021-life-stage-tables, with the use 'display'."
cadence = "One-off. Census Day 21 March 2021. Next census 2031."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.ons.gov.uk/datasets/TS021/editions/2021/versions/3",
    "https://www.ons.gov.uk/datasets/TS030/editions/2021/versions/3",
    "https://api.beta.ons.gov.uk/v1/datasets/TS004/editions/2021/versions/3",
    "https://api.beta.ons.gov.uk/v1/datasets/TS021/editions/2021/versions/3",
    "https://api.beta.ons.gov.uk/v1/datasets/TS030/editions/2021/versions/3",
    "https://www.nomisweb.co.uk/home/copyright.asp",
    "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
]
notes = "How it was verified: the ONS dataset pages for TS021 and TS030 state OGL v3.0 in the footer. The ONS data service records lowest_geography 'oa' for TS004, TS021 and TS030, 'ltla' for TS012 and TS024, and 'msoa' for TS022, TS031, TS077 and TS078. The TS030 page says: 'This question was voluntary'. A held source may have internal uses only, so no use is listed; the intended use once released is 'display'. All pages were read through a reader that summarises."
```

## Sources read

All on 2026-09-23.

| What | Address |
|---|---|
| ONS, topic summaries | https://www.ons.gov.uk/census/aboutcensus/censusproducts/topicsummaries |
| ONS data service, one record per table | https://api.beta.ons.gov.uk/v1/datasets/TS021/editions/2021/versions/3 and the same for TS003, TS004, TS005, TS007, TS015, TS024, TS025, TS027, TS029, TS030, TS031, TS068, TS077, TS078. TS012 and TS022 at `versions/2` |
| ONS dataset pages | https://www.ons.gov.uk/datasets/TS021/editions/2021/versions/3 and the same for TS003, TS030, TS077 |
| Nomis, table list | https://www.nomisweb.co.uk/sources/census_2021_ts |
| Nomis, table pages | https://www.nomisweb.co.uk/datasets/c2021ts021 and the same for `ts004`, `ts077` |
| Nomis, copyright | https://www.nomisweb.co.uk/home/copyright.asp |
| Open Government Licence v3.0 | https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/ |
| ONS, protecting personal data in Census 2021 | https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/methodologies/protectingpersonaldataincensus2021results |
| ONS, quality and methodology, Census 2021 | https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/methodologies/qualityandmethodologyinformationqmiforcensus2021 |
| ONS, sexual orientation and gender identity quality | https://www.ons.gov.uk/peoplepopulationandcommunity/culturalidentity/sexuality/methodologies/sexualorientationandgenderidentityqualityinformationforcensus2021 |
| ONS, statistical geographies | https://www.ons.gov.uk/methodology/geography/ukgeographies/statisticalgeographies |
| ONS, release plans | https://www.ons.gov.uk/census/aboutcensus/releaseplans |
| ONS, planning for Census 2031 | https://www.ons.gov.uk/census/aboutcensus/census2031/planningforcensus2031 |
| GLA, ethnic group projections | https://data.london.gov.uk/dataset/ethnic-group-population-projections |
| GLA, ward profiles | https://data.london.gov.uk/dataset/ward-profiles-and-atlas |
| Equality Act 2010, sections 4, 9, 13, 19, 26, 28, 29, 31, 32, 33, 38, 111, 112, 114, 119 | https://www.legislation.gov.uk/ukpga/2010/15/section/29 and the same for each section |
| Equality Act 2006, section 20 | https://www.legislation.gov.uk/ukpga/2006/3/section/20 |
| EHRC Code of Practice 2026, publication page | https://www.gov.uk/government/publications/equality-act-2010-code-of-practice-for-services-public-functions-and-associations-2026 |
| EHRC Code of Practice 2026, PDF, 342 pages | https://assets.publishing.service.gov.uk/media/6a0de69fe0994f7c13d7b411/EHRC_Code_of_Practice_for_services__public_functions_and_associations__2_.pdf |
| EHRC Code, explanatory memorandum | https://www.gov.uk/government/publications/equality-act-2010-code-of-practice-for-services-public-functions-and-associations-2026/explanatory-memorandum--2 |
| ICO, what is special category data | https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/special-category-data/what-is-special-category-data/ |
| ICO, fairness, bias and discrimination | https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/guidance-on-ai-and-data-protection/how-do-we-ensure-fairness-in-ai/what-about-fairness-bias-and-discrimination/ |
| ICO, introduction to anonymisation | https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-sharing/anonymisation/introduction-to-anonymisation/ |
| ICO, what is personal data | https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/personal-information-what-is-it/what-is-personal-data/what-is-personal-data/ |
| ASA, what it covers | https://www.asa.org.uk/about-asa-and-cap/the-work-we-do/what-we-cover.html |
| CAP Code, sections 3 and 4 | https://www.asa.org.uk/type/non_broadcast/code_section/03.html and `/04.html` |
| ASA advice, offence: race | https://www.asa.org.uk/advice-online/offence-race.html |
| FCA, research note and blog | https://www.fca.org.uk/publications/research-notes/motor-insurance-pricing-local-area-ethnicity-england-wales and https://www.fca.org.uk/news/blogs/motor-insurance-pricing-local-area-ethnicity |
| Redfin, on crime data | https://www.redfin.com/news/neighborhood-crime-data-doesnt-belong-on-real-estate-sites/ |
| Overture, places guide and schema | https://docs.overturemaps.org/guides/places/ and https://docs.overturemaps.org/schema/reference/places/place/ |
| Food Standards Agency, business types | https://api1-ratings.food.gov.uk/business-types/xml |
| HM Passport Office, places of worship registered for marriage | https://www.gov.uk/government/publications/places-of-worship-registered-for-marriage |
| The services in section 2 | The addresses given in that table |
