# Figures about residents, recorded crime and the equality law

**Draft. Not legal advice.** Written on 24 September 2026 from the public guidance of the Information Commissioner's Office (ICO), from the Equality Act 2010 as printed at legislation.gov.uk, and from the decision records of this repository. **Whoever wrote it is not a lawyer, and nobody qualified has read it.** There is no budget for that ([ADR 0007](../adr/0007-no-solicitor.md)).

It says what Burro holds about the people who live in an area, what the two regulators' own pages say of a product that shows and ranks on such figures, what the risk is, and what the terms forbid. Each point where a solicitor's reading would change what is safe to ship is marked `[SOLICITOR]` and listed in section 9.

| Mark | Meaning |
|---|---|
| Read twice | Read at the publisher's own address on 24 September 2026, twice, asked in different words each time. What is kept is what both readings gave. Every page was read through a reader that extracts of a page, not the page itself, so a quoted sentence may differ from the source by a word |
| Read once | Read once that day, the same way |
| Not read | The page was not read. Nothing is said of what it holds |
| `[NOT BUILT: ...]` | The code does not yet make the sentence true |
| `[SOLICITOR]` | This draft's reading of the law decides what ships. A qualified reading could change it |

## 1. In short

| Question | Answer |
|---|---|
| What does Burro hold about residents | Published counts from Census 2021, for areas of several thousand people. Nothing about any one person |
| What does Burro hold about the people who use it | Nothing. No account, no name, no record of a search. The [privacy notice](privacy-notice.md) says what passes through |
| What is ranked on | The age of an area's residents and what its households are made of, from the census, where a person asks. Nothing else about residents |
| What is shown and never ranked on | Ethnic group, religion and country of birth, as the statistics office's own table on an area's page |
| What is never read | Stop and search records. Income, employment, health, qualifications, disability, sexual orientation and gender identity stay out of ranking as before |
| Recorded crime | Counts in one vibe, Gritty, when a person asks for that vibe by name. Elsewhere it counts only when a person asks for it or switches it on |
| Is a figure about an area personal data | On the ICO's pages as read, not where nobody can be identified from it. `[SOLICITOR]` |
| Does the Equality Act reach a free website | Section 29 says "for payment or not". This draft reads that as yes. `[SOLICITOR]` |
| The main risk | That someone who lets or sells homes uses Burro to steer people by who they are. The terms forbid it, in section 7 of the [terms of use](terms-of-use.md) |
| What would make it worse | Ranking or filtering towards or away from an ethnic or religious group. It was weighed, it is kept open, and it is not built |
| What was not read | The equality regulator's own guidance for service providers. The Act was read in its place. Section 10 |

## 2. What was decided

The founder decided these on 24 September 2026. [ADR 0006](../adr/0006-rank-places-not-residents.md) and [ADR 0014](../adr/0014-evidence-first-and-census-figures-shown.md) record them.

| Matter | Decided | Built |
|---|---|---|
| The age of residents, and what households are made of | May feed a vibe and a ranking, from the census | `[NOT BUILT: no release holds a measure of either]` |
| Ethnic group and religion | Shown on an area's page. Ranked on only through what is there: places of worship, cultural centres, food shops | `[NOT BUILT: no page shows the census table, and no release counts a place of worship]` |
| Country of birth | The founder was not asked. It stands as it did: shown, and never ranked on | `[NOT BUILT]`, as above |
| Ranking towards a community a person names, and never away from one | Weighed, and kept open. Not built | Not built |
| A filter that includes or excludes an area by who lives there | Not built. Nobody asked for one | Not built |
| A wish for fewer of any group of people | Nothing reads one. This holds for age and household make-up too: a person may ask for more of what a figure counts, and never for fewer | Code and test, for every group the reader knows a word for. `test_a_request_about_who_lives_somewhere_makes_no_edit_at_all` |
| Gender | Left out. Every area is close to even | Not built, and not to be |
| Stop and search | Never read, whatever the rule on residents says | The registry's condition on `police-uk-street-level-crime` forbids it. No code reads the police file yet |
| The police file as saved | The crime files alone are read. The outcomes and the stop and search files are never opened | The same |
| The religious character of a school | It is no amenity. Schools are counted without regard to faith, and the column is never read | The registry's condition |
| Income, employment, health, qualifications | The founder was not asked. They stay out of ranking | Code and test: `test_no_feature_or_tag_describes_residents` |
| A word for how well off an area is, such as "affluent" | It is offered as a wish about the place, in two readings: towards the polished end of Gritty, or homes that sell for more than London's middle. Never income, and never who lives there | `[NOT BUILT: as the code stands such a word is answered as a wish about who lives somewhere, and makes no setting]` |
| Recorded crime in Gritty | One vibe, Gritty, counts recorded criminal damage and recorded anti-social behaviour, with works and warehouses, main roads, noise and density. To type "gritty" is to ask for recorded crime by name | `[NOT BUILT: a release that is not made up is refused if its Gritty holds recorded incidents. The rule is gritty_b_is_synthetic]` |

## 3. What Burro holds, and what it does not

| Thing | What it is | Who published it | About whom |
|---|---|---|---|
| Census tables of age and of household composition, TS007A and TS003 | Counts of usual residents by age band, and of households by kind, on 21 March 2021 | Office for National Statistics, under the Open Government Licence | An area. No row is about a person or a household |
| Census tables of country of birth, ethnic group and religion, TS004, TS021 and TS030 | Counts of usual residents by category, on the same day | The same | An area |
| Recorded crime | Counts or rates of what the police recorded, by category, for an area | The police's open data site, or a department's indicators built from police records. Which of the two feeds Gritty is not settled | An area. The police site moves each event to a point that stands for at least eight addresses or for none. Read twice |

| Burro does not hold | Why |
|---|---|
| Anything about a person who lives anywhere | Every figure is a published count for an area. Burro has no row for a person, a household, a home or an address |
| Anything about a person who uses it | There is no account. A search is not kept. The [privacy notice](privacy-notice.md), sections 2 and 6 |
| A figure for a small area | The areas Burro shows are the statistics office's middle layer areas, or named areas made of many output areas. The office says a middle layer area has "a usually resident population between 5,000 and 15,000 persons". Read twice. The design of the census table leaves a table out for an area of under 1,000 people or 400 households ([the design](../design/london-data-census.md), section 3). `[NOT BUILT: no test holds the floor, because no table is built]` |
| A count of people in a category | Shares only, as whole per cents. Under one in a hundred reads "under 1%". The registry's condition on both census entries |
| Stop and search records | They are never read. `[FOUNDER: they are not held only once no copy of a police file that holds them is kept. Section 5]` |
| A guess about you | Burro draws no conclusion about a person from what they ask for, and treats nobody differently for it. The same settings give the same ranking to everyone |

## 4. What the ICO's pages say, and what they ask of a product that shows such figures

### What was read

| Page | Address | Its own date | Read |
|---|---|---|---|
| Special category data | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/a-guide-to-lawful-basis/special-category-data/> | 28 October 2024 | Twice |
| What is special category data? | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/special-category-data/what-is-special-category-data/> | 9 April 2024 | Twice, and a third time for the words |
| What is personal data? | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/personal-information-what-is-it/what-is-personal-data/what-is-personal-data/> | None shown | Twice |
| Anonymisation: about this guidance | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-sharing/anonymisation/about-this-guidance/> | Published 28 March 2025 | Once |
| Anonymisation: introduction | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-sharing/anonymisation/introduction-to-anonymisation/> | None shown | Twice |
| Anonymisation: how do we ensure anonymisation is effective? | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-sharing/anonymisation/how-do-we-ensure-anonymisation-is-effective/> | None shown | Twice, and a third time for the words |
| Anonymisation: glossary | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-sharing/anonymisation/glossary/> | None shown | Twice |
| What is research-related processing? | <https://www.ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/the-research-provisions/what-is-research-related-processing/> | Updated 15 June 2023 | Twice |
| What is criminal offence data? | <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/criminal-offence-data/what-is-criminal-offence-data/> | None shown | Twice |

Most of these pages carry the notice: "Due to changes made by the Data (Use and Access) Act, this guidance is under review and may be subject to change."

No page of the ICO's was found that is about published statistics by name. The pages on anonymous information are the nearest, and they are written for whoever turns personal data into statistics, which is the statistics office and not Burro.

### What the pages say

| Point | The ICO's words | Page |
|---|---|---|
| Personal data is about a person who can be identified | "'personal data' means any information relating to an identified or identifiable natural person" | What is personal data? |
| The law does not reach what is anonymous | "Data protection law does not apply to anonymous information." | Anonymisation: introduction |
| What aggregated data is | "statistical data about several people that has been combined to show general trends or values without identifying people within the data." | Glossary |
| The test is what is reasonably likely | "if no means are 'reasonably likely' to be used by you or anyone else, then the information is anonymised." | How do we ensure anonymisation is effective? |
| The test is not what can be imagined | "The key is what is 'reasonably likely' relative to the circumstances, not what may be independently 'conceivably likely'." | The same. Read once |
| It can change | "You should also monitor changes in what data is publicly available as it may mean it becomes easier to re-identify data that you previously considered anonymised." | The same |
| The census is named as a thing a guess can be made from | A person may be learnt about from "other information that you either possess or may reasonably be expected to obtain (eg publicly available additional information, such as census data)" | The same. Read once |
| A guess about a person is personal data only if it is about a person | "Whether an inference is personal data depends on whether it relates to an identified or identifiable person." | The same |
| Special category data is personal data | "Special category data is personal data that needs more protection because it is sensitive." The list holds "personal data revealing racial or ethnic origin" and "personal data revealing religious or philosophical beliefs" | Special category data |
| When a guess becomes special category data | It "depends on whether: your processing intends to make an inference linked to one of the special categories of data; or you intend to treat someone differently on the basis of inferred information linked to one of the special categories of data." | What is special category data? |
| How sure the guess is does not matter | "If this is the case, then you are processing special category data regardless of how confident you are that the inference is correct." | The same |
| What statistics are for | To count as statistical, whoever does the work should either "not use the results to make decisions or justify measures about people; or render the results anonymous, making it no longer personal data." | What is research-related processing? |
| Putting results beside other data can undo them | "You should note that if you hold other information that you could combine with the anonymised results, this could re-identify linked individuals." | The same |
| Criminal offence data is personal data | It is "personal data relating to criminal convictions and offences or related security measures" | What is criminal offence data? |
| A crime against a victim who can be identified | "Information about a specific crime committed against an identifiable victim is the personal data of the victim, but we do not consider it to be criminal offence data" | The same |

### What that asks of Burro

This is this draft's reading of the pages above. No page says it of a product like Burro in these words.

| # | What the pages ask | How Burro meets it | Held by |
|---|---|---|---|
| 1 | That nobody can be identified from a figure, by any means reasonably likely to be used | Every figure is a share for an area of several thousand people, from tables the statistics office has already protected. No count is shown, and no share for fewer than 1,000 people | The registry's conditions. `[NOT BUILT: the floor of 1,000, and the test that holds it]` `[SOLICITOR]` |
| 2 | That figures are not put beside other data so that a person can be picked out | Burro holds nothing about a person to put them beside. It has no address, no name and no row for a home. The census entries carry the publisher's own term: no attempt to learn about an identified person, household or business | The registry's conditions. Nothing in code joins a census figure to anything but an area |
| 3 | That no guess is made about a person's ethnicity, religion or health | Burro makes none. It does not ask who a person is, does not work it out from what they search for, and does not treat one person differently from another | Code and test: the same settings give the same ranking. `test_rank_gives_the_same_result_every_time` |
| 4 | That results are not used to decide about a person | Burro decides nothing about anyone. The terms forbid anyone else using it to | The [terms of use](terms-of-use.md), section 7. Nothing enforces a term |
| 5 | That the reading is looked at again when more is published | The checklist asks for it every three months | [The checklist](data-protection-checklist.md), task 19 |
| 6 | That the decision is written down | This page, and the two decision records | |

**What a person types is another matter.** A sentence such as "near my mosque" or "I use a wheelchair" is about the person who typed it, and it is special category data whatever Burro holds about areas. The privacy notice, sections 5 and 11, deals with it. A setting about a place of worship can say something of a person's religion too. It is held in the browser, it is sent with each request, and it is stored if the person makes a shared link. On the ICO's words above, a setting is special category data only if Burro means to guess at the person from it, or to treat them differently. It does neither. `[SOLICITOR]`

## 5. Why stop and search data is never read

| | |
|---|---|
| What the file is | The police's open data site describes it as "Individual stop and search records, including date and time, street-level location, ethnicity, gender and age of the person stopped, and outcome". Read twice, at <https://data.police.uk/about/> |
| What is done to it before it is published | "The location coordinates of the stop are anonymised and the age of the person stopped is changed to an age group (e.g. 18-24) before publication." Read twice |
| Why it is never read | Each row is about one person on one day. It says whom the police stopped, and not who lives in a place. A count of stops by ethnic group in an area would be read as a fact about the area's residents, and it is not one |
| Does the decision on residents change it | No. The founder decided that it is never read, whatever the rule on residents says |
| What holds it | The registry's condition on `police-uk-street-level-crime`: the crime files only. The site offers the three kinds of file by three boxes on one form. `[NOT BUILT: no step reads the police file yet, so no test refuses the other two]` |
| A file saved with all three boxes ticked | It holds the records of stop and search and of outcomes beside the crime files. The founder decided that of such a file the crime files alone are read, and the rest is never opened. To keep it is still to hold it: save the file again with the crime box alone, and delete the first copy |
| What the file says of a person | A time, a place, an age group, a gender and an ethnicity are five facts about one person. Whether a row is personal data in the hands of whoever downloads it was not read at a source. Burro does not need to settle it if it holds no such file. `[SOLICITOR]` |

## 6. Recorded crime

| | |
|---|---|
| What is held | A count or a rate for an area, by category. Never an event, and never a point |
| What counts in Gritty | Recorded criminal damage and recorded anti-social behaviour, as two of its parts |
| When it counts | When a person asks for Gritty by name, towards either end. Recorded crime counts nowhere else unless a person asks for it by name or switches it on |
| What Burro says | The count, its category, its period and its source. Never "safe" or "unsafe". `test_site_copy_never_calls_a_place_safe_or_unsafe` |
| What the page of a vibe says | That the vibe counts recorded crime, and which parts of it do. The words are the website's, in `apps/web/src/content/crime.ts` |
| Is it about a person | This draft reads a count for an area as about nobody who can be identified. The ICO's page says a crime against "an identifiable victim" is the victim's personal data. The police site moves each event to a point that stands for at least eight addresses or none, and speaks of "protecting the privacy of victims". Read twice. `[SOLICITOR]` |
| What a rate is divided by | A rate that a publisher has divided by a count of residents, or has smoothed by the kind of people who live in an area, leans on who lives there. Which file feeds Gritty, and whether such a rate may, is the founder's to decide before a figure is shown. The publisher's method was not read for this draft |
| Recorded is not committed | A count says what was reported and recorded. Anti-social behaviour is recorded where it is reported. The methods page and the page of the vibe must say so. `[NOT BUILT: no release that is not made up holds the figure]` |

## 7. The equality law, as read

### What was read

Every section was read at legislation.gov.uk, where each page says that it is up to date with all changes known to be in force on or before a day between 21 and 24 September 2026.

| Provision | What it is about | Address | Read |
|---|---|---|---|
| Section 4 | The protected characteristics | <https://www.legislation.gov.uk/ukpga/2010/15/section/4> | Once |
| Sections 9 and 10 | Race, and religion or belief | <https://www.legislation.gov.uk/ukpga/2010/15/section/9> | Once each |
| Section 13 | Direct discrimination | <https://www.legislation.gov.uk/ukpga/2010/15/section/13> | Twice |
| Section 19 | Indirect discrimination | <https://www.legislation.gov.uk/ukpga/2010/15/section/19> | Twice |
| Section 28 | What Part 3, on services, does not apply to | <https://www.legislation.gov.uk/ukpga/2010/15/section/28> | Twice |
| Section 29 | Provision of services | <https://www.legislation.gov.uk/ukpga/2010/15/section/29> | Twice |
| Section 31 | What a service is | <https://www.legislation.gov.uk/ukpga/2010/15/section/31> | Once |
| Section 32 | What Part 4, on premises, does not apply to | <https://www.legislation.gov.uk/ukpga/2010/15/section/32> | Twice |
| Section 33 | Letting and selling | <https://www.legislation.gov.uk/ukpga/2010/15/section/33> | Twice |
| Section 38 | What disposing of premises means | <https://www.legislation.gov.uk/ukpga/2010/15/section/38> | Once |
| Section 111 | Instructing, causing or inducing | <https://www.legislation.gov.uk/ukpga/2010/15/section/111> | Twice |
| Section 112 | Aiding | <https://www.legislation.gov.uk/ukpga/2010/15/section/112> | Twice |
| The Explanatory Notes to sections 13, 19, 29, 33, 111 and 112 | The government's own account of each | <https://www.legislation.gov.uk/ukpga/2010/15/notes/contents> | Section 19 once, the others twice |
| The guidance of the Equality and Human Rights Commission for service providers, and its code of practice on services | | | **Not read** |
| Any judgment of a court | | | Not read |

### What the Act says

| Point | The Act's words | Where |
|---|---|---|
| The protected characteristics | "age; disability; gender reassignment; marriage and civil partnership; pregnancy and maternity; race; religion or belief; sex; sexual orientation" | Section 4 |
| Race is wide | "Race includes (a) colour; (b) nationality; (c) ethnic or national origins." | Section 9(1) |
| Religion includes having none | "a reference to religion includes a reference to a lack of religion" | Section 10(1) |
| Direct discrimination | "A person (A) discriminates against another (B) if, because of a protected characteristic, A treats B less favourably than A treats or would treat others." | Section 13(1) |
| Age can be justified, where it is direct | "If the protected characteristic is age, A does not discriminate against B if A can show A's treatment of B to be a proportionate means of achieving a legitimate aim." | Section 13(2) |
| Keeping people apart by race | "If the protected characteristic is race, less favourable treatment includes segregating B from others." | Section 13(5) |
| It need not be the person's own characteristic | "This definition is broad enough to cover cases where the less favourable treatment is because of the victim's association with someone who has that characteristic (for example, is disabled), or because the victim is wrongly thought to have it (for example, a particular religious belief)." | Explanatory Notes to section 13 |
| Indirect discrimination | A "provision, criterion or practice" that is applied to everyone, that puts people who share a characteristic "at a particular disadvantage", and that A "cannot show ... to be a proportionate means of achieving a legitimate aim" | Section 19 |
| A service that is free is a service | "A person (a "service-provider") concerned with the provision of a service to the public or a section of the public (for payment or not) must not discriminate against a person requiring the service by not providing the person with the service." | Section 29(1) |
| What a service-provider must not do | Discriminate "as to the terms on which A provides the service to B", "by terminating the provision of the service to B", or "by subjecting B to any other detriment" | Section 29(2) |
| Who a service is provided to | "A reference to a person requiring a service includes a reference to a person who is seeking to obtain or use the service." | Section 31(6) |
| Services and age | Part 3 does not apply to "age, so far as relating to persons who have not attained the age of 18" | Section 28(1) |
| Letting and selling | "A person (A) who has the right to dispose of premises must not discriminate against another (B) (a) as to the terms on which A offers to dispose of the premises to B; (b) by not disposing of the premises to B; (c) in A's treatment of B with respect to things done in relation to persons seeking premises." | Section 33(1) |
| Letting and selling, and age | "This Part does not apply to the following protected characteristics (a) age; (b) marriage and civil partnership." | Section 32(1) |
| Leading someone else to discriminate | "A person (A) must not induce another (B) to do in relation to a third person (C) anything which is a basic contravention." "Inducement may be direct or indirect." | Section 111(3) and (4) |
| Who may bring a claim | The person who was led and the person who was wronged, where each was "subjected to a detriment as a result of A's conduct", and the Commission | Section 111(5). The words were read once |
| Nobody need have been wronged | "it does not matter whether (a) the basic contravention occurs" | Section 111(6) |
| To try is enough | "A reference in this section to causing or inducing a person to do something includes a reference to attempting to cause or induce the person to do it." | Section 111(8) |
| When that applies | "This section does not apply unless the relationship between A and B is such that A is in a position to commit a basic contravention in relation to B." | Section 111(7) |
| Helping someone else to discriminate | "A person (A) must not knowingly help another (B) to do anything which contravenes Part 3, 4, 5, 6 or 7" | Section 112(1) |
| The defence of a statement | "It is not a contravention of subsection (1) if A relies on a statement by B that the act for which the help is given does not contravene this Act, and it is reasonable for A to do so." | Section 112(2) |
| A false statement is an offence | "B commits an offence if B knowingly or recklessly makes a statement mentioned in subsection (2)(a) which is false or misleading in a material respect." | Section 112(3) |

The Explanatory Notes give two examples for section 33: "A landlord refuses to let a property to a prospective tenant because of her race. This is direct discrimination when disposing of premises." None of the examples read is about a website, an estate agent or the choice of an area.

## 8. The risk, said plainly

### Who could be wronged, and by whom

| Who | How | How likely, on this draft's reading |
|---|---|---|
| A person who uses Burro, wronged by Burro | Burro treats them worse because of who they are | Low. Burro does not know who anyone is, asks nothing about them, and gives the same ranking for the same settings. It would have to guess at a person from what they type, and it is built not to |
| A person who uses Burro, wronged by a rule that falls harder on people like them | A setting that nobody chose, or a measure, that ranks lower the areas where people of one group mostly live | Not known. It is what the proxy audit is for, and the audit is not built. `[SOLICITOR]` |
| A person looking for a home, wronged by someone who lets or sells homes | An agent or a landlord uses Burro to choose which areas to offer to which people, by race, religion or another protected characteristic | This is the main risk. The wrong is the agent's. Burro is drawn in if it knew, or if it led the agent to it |
| The people who live in an area | The area is ranked low, or is shown with figures about them | They are not the people Burro provides a service to, so section 29 as read does not give them a claim. The harm is real all the same: to how an area is spoken of. [ADR 0014](../adr/0014-evidence-first-and-census-figures-shown.md) names a complaint from residents as a thing that would change the decision |

### What this draft reads the Act to mean for Burro

| # | Reading | Mark |
|---|---|---|
| 1 | Burro is a service-provider. It offers a service to the public, and section 29 says "for payment or not" | `[SOLICITOR]` |
| 2 | Showing the statistics office's table of ethnic group and religion on an area's page treats no person less favourably. Everyone is shown the same table | `[SOLICITOR]` |
| 3 | Ranking on the age of residents and on what households are made of treats no person less favourably. It ranks areas at the request of the person who asks, and the person's own age is never known | `[SOLICITOR]` |
| 4 | Age is treated more gently by the Act than race or religion. Direct discrimination by age can be justified. The part on letting and selling does not apply to age at all. The part on services applies to age for adults | As read |
| 5 | Race is treated most strictly. To segregate by race is less favourable treatment in itself, and the Explanatory Notes say that "racial segregation is always discriminatory" | As read |
| 6 | Burro does not help anyone to discriminate "knowingly", because it knows nothing of who uses it or why. A product that was sold to letting agents as a way to find areas by who lives there would know | `[SOLICITOR]` |
| 7 | Section 111 could reach Burro. Burro provides a service to whoever uses it, so it is in a position to contravene Part 3 in relation to them, which is what section 111(7) asks. If Burro led an agent to steer people, directly or not, that could be inducing. As printed it is enough to try, nobody need have been wronged, and the regulator may bring the claim itself. So what Burro says of itself matters as much as what it does. Nothing in Burro invites it, and the terms forbid it | `[SOLICITOR]` |
| 8 | A term of use is a statement by whoever uses Burro in the course of a business that they will not use it to discriminate. Whether a term that nobody signs is a statement Burro may reasonably rely on, as section 112(2) asks, is not settled | `[SOLICITOR]` |

### What keeps the risk down, in the product and not in words

| What | Held by |
|---|---|
| Nothing can search, sort, filter or colour a map by ethnic group, religion or country of birth | [ADR 0014](../adr/0014-evidence-first-and-census-figures-shown.md). `test_no_feature_or_tag_describes_residents` |
| The census table is the office's own figures, in its own words and order, with no sentence of Burro's, no "main" group, no comparison and no colour | ADR 0014. `[NOT BUILT: no page shows the table]` |
| The table is on an area's page and nowhere else: not in a result, a reason, a comparison, a likeness or a shared link | ADR 0014. `[NOT BUILT]` |
| Nothing reads a wish for fewer of any group. A person who asks is told so in one sentence, and the rest of what they asked is answered | `test_a_request_about_who_lives_somewhere_makes_no_edit_at_all` |
| A wish for a community is met through what is there | [ADR 0006](../adr/0006-rank-places-not-residents.md) |
| A figure of age or of households can be asked for more of, and never for less. It is no end of a scale and no filter | The registry's condition. `[NOT BUILT]` |
| Burro shows no home, links to none and takes no money from anyone who lets or sells | [The plan](../PLAN.md): section 15 says that it links to no listing, and section 2 that it is independent of estate agents' revenue. A promise. That it takes no money from them is the founder's to confirm, in the [terms of use](terms-of-use.md), section 2 |
| The same settings give the same ranking to everyone | `test_rank_gives_the_same_result_every_time` |
| Burro asks nobody who they are | No account, and no question. The privacy notice, section 2 |

### What would make it worse

| What | Why | Built |
|---|---|---|
| Ranking towards or away from an ethnic or religious group | Burro would then sort areas by race or religion on request. Whoever ran it for a customer would be steering by race with Burro's help, and Burro could no longer say it did not know what the control was for. The Explanatory Notes say racial segregation is always discriminatory | No. Ranking towards a community is kept open. Ranking away from one was never proposed |
| A filter that includes or excludes areas by who lives there | The same, more bluntly | No |
| Reading a wish for fewer of any group | It is steering away, asked for in words | No |
| A sentence of Burro's own about the figures, a label for an area, or a colour on a map | It turns the office's table into Burro's verdict on who an area is for | No |
| Asking a person who they are, or guessing it | Burro could then treat people differently, and would hold special category data about them | No |
| Showing homes, or taking money from those who let or sell them | Burro would then be "concerned with" letting and selling, and nearer to section 33 | No |
| Selling Burro to agents as a way to find areas by who lives there | It is inducing, said out loud | No |
| A figure for a very small area | A share for a few dozen people can point at a household | No |
| A rate of recorded crime that has been divided or smoothed by who lives there | It brings residents into a measure that is said to be of the place | Not settled. Section 6 |

## 9. Where a solicitor's reading would change what is safe to ship

In the order of what each could cost. "Ships today" means what this draft's reading allows. Nothing is deployed.

| # | The point | This draft's reading | What ships on that reading | What another reading would change |
|---|---|---|---|---|
| 1 | Whether ranking on the age of residents, or on what households are made of, can be discrimination by Burro | No. Areas are ranked, not people, and the person's own age is never known | Age and household make-up feed a vibe when a person asks | They would be shown and not ranked on, as ethnic group is. One change to the registry and the catalogue |
| 2 | Whether the census table of ethnic group and religion, on the page of an area that Burro also ranks, leads anyone to steer | No, as it is shown: unranked, unlabelled, on the area's own page | The table is shown | It would be taken off, or moved behind a link to the statistics office |
| 3 | Whether Burro is a service-provider at all, and whether section 111 reaches it | Yes to the first. Possibly to the second | Nothing changes: the design assumes both | If neither, the term on letting and selling could be shorter. It would still be kept |
| 4 | Whether a term of use is a statement Burro may rely on under section 112(2) | Not settled | The term is in the terms of use all the same | A step that asks a business to agree before it uses Burro, which needs a way to tell a business from a person |
| 5 | Whether a figure for an area of several thousand people can be personal data | No, where no count is shown and no share is for fewer than 1,000 people | Shares for areas | A higher floor, or fewer categories |
| 6 | Whether a setting about a place of worship is special category data | No, because Burro guesses nothing from it and treats nobody differently | Settings are held in the browser, sent with each request, and stored in a shared link on request | The step that asks before a sentence is sent would have to cover settings and shared links too |
| 7 | Whether a count of recorded crime for an area is personal data of a victim or criminal offence data | No, for a count by area | Counts and rates by area | Less detail by category, or larger areas |
| 8 | Whether a measure with no word about residents still falls harder on one group | Not known | Every measure that is built | A measure would be dropped, capped or made to count only on request, by the rule of the proxy audit |
| 9 | Whether a copy of the police file that holds records of stop and search, kept and never opened, is personal data that Burro holds | Not settled | The crime files alone are read | Nothing, once the file is saved again without them, which section 5 asks for in any case |
| 10 | Whether to say "gritty" of an area harms the people who live there | Not read at any source. The name of a vibe is a word about land, roads and what was recorded, and a person asks for it | The vibe is called Gritty | Another name, or no band shown on an area's page |

## 10. What was not read, and what to do about it

| What | Why it matters | What to do |
|---|---|---|
| The Equality and Human Rights Commission's guidance for service providers, and its code of practice on services, public functions and associations | It is the regulator's own account of what a service-provider must not do, and it may speak of estate agents and of steering. Nothing of it is in this draft | The founder opens it in a browser at <https://www.equalityhumanrights.com> and reads the parts on services and on premises. One hour. It is task 8 of [the checklist](data-protection-checklist.md) |
| Any judgment on steering, or on a website as a service-provider | The Act's words are wide, and courts decide what they reach | A qualified reading |
| Schedule 3 and Schedule 5 of the Act, which hold the exceptions | An exception may help or may not apply | A qualified reading |
| Part 7 of the Act, and sections 108 to 110 | Section 111 names them | A qualified reading |
| The statistics office's account of how it protects census tables | This draft rests on the registry's note of it, which says that records are swapped between nearby small areas and that small changes are made to counts | Read the office's page before the census table is shown |
| The method behind any rate of recorded crime that is not the police's own count | Section 6 | Read it before a figure is shown |
| The ICO's helpline | It answers questions and reviews no document | Put question 4 of the [README](README.md) to it, in writing |

## 11. Words for the methods page

The website's methods page is outside this draft. It said that nothing that describes who lives somewhere is used, which stopped being true on 2026-09-24, when core came to hold four measures of age and of households. The page was changed that day to the words of the first two rows below, but for the year of the census, which the name of each measure gives. The fourth row is not written. These are the words as they were drafted. Each figure and each name is the API's to give, as now.

| Where | Today | Once a release holds a measure of age or of households |
|---|---|---|
| How the ranking works | "Burro ranks places by what is there. Nothing that describes who lives somewhere is used." | "Burro ranks places by what is there. Of the people who live in an area it counts two things, and only when you ask: how old they were and what their households were made of, at the census of 2021. It counts nothing else about who lives anywhere, and you cannot ask for fewer of anyone." |
| What is measured | "Each feature describes a place, its buildings or what was recorded there. None describes who lives there." | "Each feature describes a place, its buildings, what was recorded there, or who lived there at the census. A feature about residents says so in its name, and is of their age or their households and nothing else." |
| Vibes | "It is named for the place, not for who lives there." | The same. A vibe that counts residents says so on its card, as a vibe that counts recorded crime does |
| A new part: what Burro holds about residents | | "Burro holds published counts from Census 2021 for areas of several thousand people. It holds nothing about any person who lives anywhere, and nothing about you. The figures for ethnic group, religion and country of birth are shown on an area's page as the statistics office's own table. They are never used to rank, to filter or to colour a map. Burro never reads the police's records of stop and search: they say whom the police stopped, not who lives in a place." |
| Recorded crime | "Recorded crime counts only when you ask for it by name, switch it on in the settings, or ask for a vibe whose recipe holds it." | The same. The page of vibes names Gritty as the vibe that holds it, from the API |
