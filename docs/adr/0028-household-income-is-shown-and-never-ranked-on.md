# 0028. Household income is shown on an area's page, and no area is ranked on it

Status: accepted in part, 2026-09-24. The founder decided that the figure is fetched, shown and checked against, and that no area is ranked on it. Where it stands on the page and in what words are proposed here, and are the founder's to approve. Nobody has reviewed the words. Amended on 2026-09-25: the proxy audit is dropped ([0006](0006-rank-places-not-residents.md), as amended that day), so what the check found is held to no line of it. What is left open of the check is the founder's own choice about the higher council tax bands.

## Context

The founder asked for a reading of "affluent", was offered the statistics office's estimates of household income to check such a reading against, and answered: fetch it, show it on the area's page, and hold off ranking on it.

The figure describes residents: what the households of an area are estimated to have. [0006](0006-rank-places-not-residents.md) keeps such a figure out of every score, tag, vibe and filter. The licence registry holds the source for `display` and `validation_only` and for nothing else. Its entry asked for this record before the figure is shown, and said that the contract had no place for a figure that is shown and is no measure.

## Decision

**Household income is shown on the page of an area, as its publisher gives it, and is used for nothing else. No route ranks on it, compares on it, or explains by it.**

| | |
|---|---|
| Where it stands | On the page of an area, after every figure of the place, in a block of its own beside the census figures. It is closed until it is pressed, and the figure is asked for only then |
| What is shown | The publisher's estimate for the area, under the publisher's name for the kind of income, "Total annual household income". Its lower and upper confidence limits. The year it is of. That it is an estimate from a model, in the publisher's words. The publisher's credit and the licence |
| What is said of it | That it is a mean and no median, and of the area and of no household or person. What the publisher says of a confidence interval. That it is of one year, and no change over time is shown |
| What stands beside it | Nothing: no other area, no figure of the whole city, no rank, no band, no colour, and no word of Burro's for how well off an area is |
| Which kind of income | The first of the publisher's four: total annual household income. The three of disposable income are never read |
| Where it is kept | In a folder of its own beside the release, named for it with `-income` after. It is no file of a release, as the census is none ([0014](0014-evidence-first-and-census-figures-shown.md)) |
| What keeps it out of ranking | Structure, and not care. Core's module for it is imported by nothing in core. It is no feature, vibe, cost or fact. The gate refuses its file for scoring. One route serves it, for one area, and takes nothing. Contract, sections 2.11 and 9.7 |
| What it is checked against | The measures that are offered for a word for how well off a place is. What a check works out joins no release |

## What the check found

The three measures were held against household income across London's areas, in a folder that is never committed, as rank correlations. No figure of any area is given here.

| Measure | Areas | Rank correlation with household income |
|---|---|---|
| Homes in council tax bands E to H, as a share of homes | 982 | 0.71 |
| Median price paid for a home, of any kind | 1,002 | 0.58 |
| Median price paid for a flat, from the sales of three years | 984 | 0.32 |
| The mix of brands, as another branch measures it | 990 | 0.45 |
| Price rise over five years | 1,002 | 0.04 |
| Price rise over ten years | 1,002 | -0.13 |

**Two of them follow household income more closely than the rest**: the council tax bands, and what homes of any kind sell for. Each is a figure of the homes of a place, and each follows what the households there are estimated to have. What is done today, and what is the founder's to decide, is in the last section.

**Amended, 2026-09-25.** This section said that the two are at or over the line that the rows of the proxy audit set, which was 0.5, and that [0006](0006-rank-places-not-residents.md) holds that finding a correlation and doing nothing is worse than not looking. The founder dropped the proxy audit on 2026-09-25. No line is set, and no figure of this table triggers a review. The table stands as what was measured.

## Consequences

- **A person can read what the households of an area are estimated to have**, with the limits the publisher puts round it, and with the publisher's own caveats.
- **Nothing of a search changes.** The ranking, a comparison and the reasons are the same, byte for byte, with the figures of every area handed to the next area, and with none served. A test holds each.
- **The page of an area holds a second block about who lives there.** It is asked for apart, is never kept by a browser, and is never in the page as it is built.
- **The contract has a place for a figure that is shown and is no measure.** The next such figure follows it.
- **The iPhone app shows none of it yet.** Its models know the route. No screen asks for it.

## What is not settled

| Matter | Whose | What stands today |
|---|---|---|
| The words of the block | The founder's | Those of `ONS` in core's `income.py`. Each line that quotes the publisher is quoted from the workbook |
| Whether the share of homes in the higher council tax bands may still be asked for, now that it is known to follow household income at 0.71 | The founder's own choice, which they make after looking at the figure | It is offered for a word for a smart area and never applied. It stands in no vibe and in no likeness, and nothing weighs it by default. What can be done: show it and rank on it no longer, or leave it as it is served today. Until 2026-09-25 this row asked the same of what homes sell for, under the line of the proxy audit. The line went with the audit, and what homes sell for stays as it is served |
| Whether the figure is ever ranked on | The founder's, by a new record | It is not. The registry entry lists no scoring |
| The credit | A person's, by opening the workbook | "Source: Office for National Statistics", as the workbook's terms ask. `attribution_verified` stays false until a person has read it |
