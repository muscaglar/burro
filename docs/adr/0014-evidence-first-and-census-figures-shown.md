# 0014. Evidence first, and census figures are shown

Status: accepted, 2026-09-23. It amends [0002](0002-deterministic-core.md) and [0006](0006-rank-places-not-residents.md), and changes sections 9 and 15 of the plan. The number 0013 is kept for the record on vibes. Amended the same day, for the founder to approve: the third sentence of rule 8 is reworded, and the registry's heading and use are named. See "Rule 8, reworded" below.

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

## Consequences

- The plan's promise not to show these figures is withdrawn. Sections 9 and 15 change with this record.
- Burro can now be criticised for printing ethnicity beside a tool that ranks areas. The answer is in how it is shown: the official figures, unranked, unlabelled, on the area's own page, with nothing in the product able to search or sort by them.
- No professional has read this. [0007](0007-no-solicitor.md) still holds: there is no budget for paid advice. The founder has taken the decision knowing that.
- Building a release becomes the larger part of the work: many sources, all of London, each record with its evidence.
- Using a model to research costs money at build time and nothing at answer time.

## What would change it

- Advice from someone qualified that the table should be shown differently, or not at all.
- A complaint from residents about how their area is shown.
- Evidence that people use the table to avoid areas. There is no way to search by it, so this would show up only in what people say.
