# 0014. Evidence first, and census figures are shown

Status: accepted, 2026-09-23. It amends [0002](0002-deterministic-core.md) and [0006](0006-rank-places-not-residents.md), and changes sections 9 and 15 of the plan. The number 0013 is kept for the record on vibes. Amended the same day, for the founder to approve: the third sentence of rule 8 is reworded, and the registry's heading and use are named. See "Rule 8, reworded" below. **Amended on 2026-09-24** by [0006](0006-rank-places-not-residents.md): age and household type may feed a vibe and a ranking. Country of birth, ethnic group and religion are shown and never ranked on, as before. See "Amended, 2026-09-24", below. Amended again on 2026-09-24, for the founder to approve: what stands beside a figure, and how a small number is said. See "How the figures are shown, as built" below.

## Context

The founder made three decisions on one day.

1. **Show census figures on area pages.** Until now the plan said Burro would not show ethnicity, religion or age breakdowns, "even for information". That line was drawn because nobody qualified had read the question, and the cautious answer cost nothing while there was no product. The founder has now weighed it and decided that a person choosing where to live should be able to read who lived in an area at the last census.
2. **Every insight is consistent and cited.** In the founder's words: "we want to ensure we're always returning consistent and cited insights. Even if not exposed to the user, these should be present and known before we reach conclusions." The founder is willing to rely on a language model's knowledge where data runs out, under that condition.
3. **All of London in the first version.** Not a pilot borough.

## Decision

### Evidence first

- Nothing is said about a place unless a stored record stands behind it. The record names its source, the date of the data, the date it was retrieved, and how the figure or sentence was derived. This holds whether or not the screen shows the source.
- A language model may be used when a release is built, to find, extract and draft. What it produces enters a release only as a claim tied to a source that code has fetched and checked: the address, the date retrieved, and the words or figure the claim rests on, found in the source as written. A claim with no source that checks out is dropped. It is never shown and never scored.
- A language model is never asked about a place at the moment of answering. What it would say then is not the same twice, and cannot be cited. This part of [0002](0002-deterministic-core.md) stands.
- There is no fallback to uncited text. Where no source says anything of an area, Burro says nothing. The founder was offered text from a model shown with a label that it was not checked, and chose against it: beside checked text a person cannot be relied on to tell the two apart.
- A release is the unit of consistency. The same question asked of the same release gives the same answer, with the same sources behind it.
- Coverage is measured. For every area and every thing Burro measures, a release says whether there is a record, and a report says what share of London each source covers. A gap is a defect that is counted, and missing data is still never filled in.

### Census figures are shown, and never ranked on

- An area's page shows figures from Census 2021 about the people who lived there: age, household type, country of birth, ethnic group, religion and main language, where the statistics office publishes them for areas of that size.
- They are shown as a table of the office's own figures, in its own categories, in its own words and order. Burro writes no sentence about them. It names no "main" group, makes no comparison with an average, and uses no colour to mark one group from another. A share under one in a hundred reads "under 1%".
- The table is headed with what it is and when: Census 2021, taken on 21 March 2021. It says that the census was taken during a lockdown, and that an area can change.
- The figures appear on an area's page and nowhere else. They are not in a search result, a reason, a trade-off, a vibe, a filter, a map layer, a comparison, a likeness between areas, or a shared link. The reader makes no edit from a request about who lives somewhere, as before, and its notice does not point to the table.
- Ranking still describes places and never residents. The first two sentences of rule 8 of AGENTS.md stand as written. No figure about residents feeds a score, a tag or a vibe.
- The figures are held under their own heading in the licence registry, apart from the sources that may be scored, so that the gate can keep them out of scoring by rule and not by care. The heading is `residents`, and its one use is `census_table`.

### Rule 8, reworded

The third sentence of rule 8 said that protected-characteristic data is registered as `audit_only`. That left no honest place for a table that is shown. It now names the second place, and what the gate lets it into.

| | Third sentence of rule 8 |
|---|---|
| Before | Protected-characteristic data is registered as `audit_only`, which the gate keeps out of scoring. |
| After | Protected-characteristic data is registered as `audit_only`, which the gate keeps out of scoring, or under `residents` for the one use `census_table`, which the gate lets into the census table on an area's page and nothing else. |

- A source under `residents` may list `census_table` and no other use, not even one for looking at a file. It may name only the five tables that are shown.
- No source under another heading may list `census_table`.
- `display` was not used for the table. A file of a release already asks the gate for `display`, so the gate itself would have let a table into a release.

### All of London

- The first version covers every part of Greater London. Every home in London falls in exactly one named area.
- A release is not fit to launch while any area lacks what a result needs to be honest: a name, a boundary, travel times, a cost range, and enough of what is measured to be ranked.

## Amended, 2026-09-24

The founder decided that two of the tables this record shows may also feed a vibe and a ranking. [0006](0006-rank-places-not-residents.md) records the decision. What it changes here:

| This record said | Now |
|---|---|
| Census figures are shown, and never ranked on | True of country of birth, ethnic group and religion. Age and household type may feed a vibe and a ranking, where a person asks for more of what a figure counts |
| The figures appear on an area's page and nowhere else | True of country of birth, ethnic group and religion. A measure of age or of households may stand wherever a measure stands: a result, a reason, a vibe, a comparison. It says in its name who is counted, and beside it that it is from Census 2021 |
| The first two sentences of rule 8 stand as written. No figure about residents feeds a score, a tag or a vibe | Rule 8 is reworded in 0006 |
| The heading `residents` has one use, `census_table` | A source under `residents` may list `scoring` as well, where every table it names is of age or of household composition |
| The reader makes no edit from a request about who lives somewhere | It makes none from a wish for fewer of any group, and none from a wish about ethnic group or religion. A wish for a community is met through what is there |

What stands: the table is the statistics office's own figures, in its own categories, words and order. Burro writes no sentence about it, names no "main" group, makes no comparison and uses no colour. Nothing can search, sort, filter or colour a map by ethnic group, religion or country of birth.

Main language is not shown for an area. The registry records that the office publishes that table for local authorities only.

## Consequences

- The plan's promise not to show these figures is withdrawn. Sections 9 and 15 change with this record.
- Burro can now be criticised for printing ethnicity beside a tool that ranks areas. The answer is in how it is shown: the official figures, unranked, unlabelled, on the area's own page, with nothing in the product able to search or sort by them.
- Since 2026-09-24 it can also be criticised for ranking on who lives somewhere at all. The answer is in what is ranked on, age and households and nothing else, in which way, towards more and never fewer, and in the terms, which forbid anyone who lets or sells homes from using Burro to steer people. [The reading of the law](../legal/residents-crime-and-equality.md) says what is left over.
- No professional has read this. [0007](0007-no-solicitor.md) still holds: there is no budget for paid advice. The founder has taken the decision knowing that.
- Building a release becomes the larger part of the work: many sources, all of London, each record with its evidence.
- Using a model to research costs money at build time and nothing at answer time.

### How the figures are shown, as built

Amended on 2026-09-24, when the part of an area's page that shows the figures was built on the made-up city. The founder decided that day that the age of residents and the make-up of households may feed a vibe, and that ethnic group and religion are shown and never ranked on. Country of birth is shown and never ranked on, as before. What was built keeps every fence of this record, and parts from "Census figures are shown, and never ranked on" in four places. **Each is for the founder to approve**, and each is one field of a record or one rule of a style sheet, so that taking it out is a small change.

| As first written | As built | To go back |
|---|---|---|
| A share, and no count | A share with the number counted beside it. A share under 1 in 100 is said in words, and its count is never given. A table is left out where fewer than 1,000 were counted, so no count under 10 is ever printed | Take `count` out of `CensusPanelRow` |
| No comparison with an average | Beside each share is the share of the whole city for the same thing, and nothing else: no other area, no borough, no rank, and no word about which is the greater | Take `city_share` and `city_percent` out of `CensusPanelRow` |
| No picture of a figure | Beside each share is the same share drawn, as a bar, with a mark for the city. It is drawn in the colour of the text, alike for every row of every table, and is kept from a screen reader | Take `Picture` out of `CensusPanel` |
| "under 1%" | "fewer than 1 in 100" | One constant, `FEWER` |

What stands as it was written:

- The publisher's own categories, in its words and its order. Nothing is ordered by size.
- Burro writes no sentence about a figure, and names no main group. A list of words Burro never uses of a figure is held in code, and a test reads every word of the part against it.
- The figures are on an area's page and nowhere else. They are in no result, reason, trade-off, filter, map layer, comparison, likeness or shared link, and the reader makes no edit from a request about who lives somewhere.
- The figures of ethnic group, religion and country of birth feed no score, no tag and no vibe. A measure of age or of households that feeds a vibe is a feature of the catalogue, with a source of its own under a heading that may be scored. It is never read from the census of an area's page.
- The part says which census it is, the day it was taken, that it was taken during a lockdown, and that an area can change.

What the publisher says of small counts, as its two pages on the matter were read on 2026-09-24: it names counts of nought, one and two as small, says that about 14 in 100 counts were changed by a small amount, and gives no figure under which a count is withheld or is not to be relied on. So the two figures above, 1 in 100 and 1,000, are Burro's own, and a first guess.

The registry's entry for the census tables still holds the conditions as first written: shares only, no count, no comparison. A real census cannot be written until the entry and this record say the same. Nothing of the registry was changed with this amendment.

## What would change it

- Advice from someone qualified that the table should be shown differently, or not at all.
- A complaint from residents about how their area is shown.
- Evidence that people use the table to avoid areas. There is no way to search by it, so this would show up only in what people say.
- The equality regulator's guidance for service providers, once a person has read it. It was not read for this record or for its amendment.
