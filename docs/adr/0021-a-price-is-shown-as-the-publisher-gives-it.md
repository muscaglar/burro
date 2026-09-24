# 0021. What a home sells for is shown as the publisher gives it: one number, with no range

Status: accepted in part, 2026-09-24. That a price may be shown is the founder's decision of that day. How a release carries it changes the contract, so that part is proposed, and is the founder's to approve. Four points are left for the founder to decide. It follows [0002](0002-deterministic-core.md), [0006](0006-rank-places-not-residents.md) and [0014](0014-evidence-first-and-census-figures-shown.md).

## Context

A person who is buying names a budget and a kind of home: up to £400,000 for a one-bedroom flat. No release of London held a cost, so the budget met no figure in any area.

The Office for National Statistics publishes the median price paid for homes in each middle layer super output area, which is what an area of a preview build is. The registry held the workbook to check Burro's own figures against, and for nothing wider. The contract held a cost as a range: a lower quartile, a median and an upper quartile, with a confidence that counts the sales behind it.

What the workbook gives, and what it does not:

| It gives | It does not give |
|---|---|
| The median price paid, for a home of any kind and for each of four kinds: detached, semi-detached, terraced, and a flat or a maisonette | A quartile, or any other sign of how widely prices spread |
| A figure for every year that ends with a quarter | How many sales stand behind a figure. It gives a figure from 5 sales up |
| `[x]` where there were no sales of a kind of home in the year, or fewer than 5 | A price by bedrooms, by floor area or by any other size |
| A credit to give, and the licence it is given under | A rent |

For the year ending March 2026 it holds a figure for a home of any kind in each of the 1,002 areas of London, for a flat in 927, for a terraced house in 873, for a semi-detached house in 549, and for a detached house in 195.

## Decision

**What a home sells for may be shown.** The founder decided so on 2026-09-24. The registry entry `ons-median-house-prices-msoa` gains the uses `scoring` and `display`. The publisher's dataset page states the Open Government Licence v3.0, which allows use in a commercial product with a credit. The credit is the publisher's own, read from the cover of the workbook: "Source: Office for National Statistics. These statistics were adapted from data from the HM Land Registry licensed under the Open Government Licence v.3.0." `registry/evidence/` holds a note of what was read and how.

**A cost is a range, or one number where no range is known.** A row of `cost.json` holds both quartiles or neither.

| A row is | `lower_quartile`, `upper_quartile` | `confidence` | `as_of` |
|---|---|---|---|
| A range, which Burro works out | Both | `high`, `medium` or `low` | The month of the estimate |
| One number, which a publisher gives | Both `null` | `unstated` | The last month of the twelve the sales were made in |

One number is a price to buy, carried as the publisher wrote it, to the pound. It is never made into a range, and it is not rounded. `unstated` says what it rests on: the publisher's word, with no count of sales behind it. Core refuses a row that holds one quartile and not the other, a row with no range that says any other confidence, a row with a range that says `unstated`, and a rent with no range.

**A budget is held against the median, as it is written.** Where a cost has no range, the engine holds the budget against the median where it held it against the upper quartile: `budget_held_against`. A firm budget leaves out an area whose median is over it. A soft one ranks a dearer area lower, down to nothing at a quarter over. Being further under the budget earns nothing, as before. The engine that does so is 1.10.0. No result moves on a release whose costs all have a range.

**A price is never scaled to a size of home.** The workbook gives no price by bedrooms. A buyer who names a one-bedroom flat is held against the median of flats of all sizes, and the sentence beside the figure says what it is of:

> Price for a flat: £{median}. This is the middle price of flats of all sizes sold in the year ending March 2026. The publisher gives no range, and does not say how many sales it rests on.

> The middle price of flats of all sizes is £{margin} under your budget of £{amount}.

The sentence prints no word for a confidence. A figure for a one-bedroom flat would be a guess at what one bedroom costs, and no figure is a guess.

**An area with no figure is ranked with its cost not known.** Where the publisher withheld the figure, or holds no row for the area, the release holds no row. The area is not left out by a budget and is not ranked as if it were cheap: the budget is dropped from its score, a firm budget is listed as not tested, and a sentence says that there is no cost figure. It is ranked on the rest of what was asked, and since [0024](0024-an-area-with-no-figure-for-what-was-asked-stands-below.md) it stands below every area whose cost is known. Where the budget is more than half of that, by weight, the area is not ranked at all: it is listed as lacking data, with the budget named as what it lacks, and never as over the budget. Its row of evidence says why there is none: `suppressed`, or `source_gap`.

**The row of evidence holds the median.** The check of a release holds the figure to its row, as it does for a measure. So a price that is changed after a build is found, and so is one that is added where the publisher gave none.

**A release holds no rent.** Rents are published for boroughs and for postcode districts, and not for areas. No design holds the model that would bring one to an area, and a figure of a larger area is never pasted onto a smaller one. A renter's budget is turned away as `not_in_release`: what a release holds for no area cannot be asked for (contract, section 5.3, rule 15).

**A price is no verdict.** It says what homes sold for. It says nothing of a place, or of who lives there. It is a cost and no measure: core's catalogue has no feature for a price, so no vibe and no likeness can rest on one. Whether a person may ask for homes that sell for more was another decision, and was not made here: see the amendment below.

**A home of any kind is not carried as a cost.** The contract holds a price by kind of home, and a budget names a kind. The median for a home of any kind is read, and is no cost of a release. Since the amendment below it is a measure of one.

**Amended, 2026-09-24: a person may ask for homes that sell for more.** The founder decided that a word for a smart area, "affluent", "posh", has two readings, both of the place: the polished end of Gritty, and homes that sell for more than the middle of the city. Neither is what people earn, and neither is who lives somewhere. So core's catalogue gains one feature for a price, `price_median`: the median price paid for a home of any kind, in pounds, as the publisher gives it for the area. It is held to four rules. It is offered and never applied from a word: a person presses "Dearer". It stands in no vibe, and a recipe that held it would be a new decision. No likeness is counted on it. Nothing weighs it by default. It is a measure like any other in every other way: it has a row of evidence, its source is credited, and a build leaves it out where the workbook was fetched to validate against and for nothing wider. The medians of the four kinds of home are costs as before, and a budget is held against them.

What was not taken:

| Way | Why not |
|---|---|
| Put the median in all three fields of a range | It says that every home sold for one price. A client would draw a range with no width, and a person would read it as certainty |
| Work a range out from the median | No source gives the spread. Any range would be made up |
| Scale the median for flats to a one-bedroom flat | No file gives what a bedroom adds. The census counts homes by bedrooms, and counts no price |
| Call the confidence `low` | `low` says a figure was modelled. This one was counted, by its publisher, from sales nobody has counted for us |
| Round the median to 5,000, as an estimate is | A reader who opens the publisher's sheet must find the number that is shown |
| Give a price a file of its own in a release | A budget is held against a cost, and a second kind of cost would need a second rule in every client |
| Carry a price as a feature of the catalogue | A feature can be a part of a vibe and of likeness. A price would then say what a place is like |
| Show a borough's rent beside an area | It is a figure of a larger area, and reads as the area's own |
| Hold a firm budget against a lower figure than the median | The workbook gives none |

## What is not settled

Each is the founder's to decide.

**1. The file was fetched to validate against, and its receipt says so.** A receipt records what the licence gate was asked when a file was fetched. The check of a release refuses a figure that rests on a file fetched for an internal use, and the first receipt of a file stands: fetch writes no second one for the same bytes. So a build of the files as they stand leaves the cost out, by the rule `input_has_one_receipt`, and says that a receipt for `validation_only` is in the folder. Three ways are open:

| Way | What it costs |
|---|---|
| A person removes the receipt, in the repository and beside the file in the store, and the file is fetched again for `scoring` | The guide to builds has the steps, under "Put a receipt right" in section 7, and allows them for a wrong edition or period and for nothing else. It would have to allow them for a use that was widened. The history of the repository keeps the first receipt |
| A receipt gains a record of a later ask: the gate was asked again, on a day, for a wider use, and allowed it | A change to the record of a receipt and to the check. It keeps every receipt as it was written |
| Wait for the next edition, in March 2027, and fetch that for `scoring` | No price is shown until then |

**2. A firm budget against a median may leave out an area where homes sold within it.** Half of the homes behind a median sold for no more than it. With a firm budget of £400,000 for a flat, 397 of the 927 areas with a figure are left out, 530 are kept, and the 75 with no figure are kept with the cost not known. In an area that is left out, flats may still have sold within the budget, and the workbook does not say whether they did, or whether a one-bedroom flat is among the cheaper half. Two other ways are open. A firm budget could never leave an area out on a median, and rank it lower. Or it could be held against the lower quartile, the price a quarter of the homes sold for no more than, which the publisher gives for each area as a dataset of its own: it is registered as `ons-lower-quartile-price-paid-msoa` and listed to be fetched, and no step reads it. As built, firm means firm, and the median is what is held.

**3. How steady a median is.** A figure of 5 sales cannot be told from one of 500. The publisher gives the count of sales for each area and kind of home as a dataset of its own. It is registered as `ons-residential-property-sales-msoa` and listed to be fetched, and no step reads it. With it a row could say `high` or `medium` by the contract's own counts. The contract has no word for a figure of 5 to 9 sales, which is fewer than `medium` counts.

**4. What HM Land Registry is due.** The cover of the workbook gives one sentence on HM Land Registry, which the credit repeats. Whether HM Land Registry asks for a statement of its own beside a figure that another publisher adapted from its data is not known.

## Consequences

- `contracts/openapi.json` changes: two quartiles and `BudgetFit.upper_quartile` may be `null`, `Confidence` gains `unstated`, and `TemplateId` gains three. The website and the iPhone app read a quartile as a number, so each must draw one number where a range is not given, before either is served a release of London. Their generated types and recorded answers are made again from the contract.
- The synthetic release is not changed: every cost in it is a range.
- When areas are drawn by hand, no sheet of the workbook holds a row for one. A price is then worked out from sales, under `hmlr-price-paid`, and can be a range with a count behind it. The rows of this record give way to those.
- The design of the data for London says the workbook is never shown. It was written before the decision, and this record stands in its place on that point.
