# 0041. A search may be a visit, which holds no budget and no home

Status: accepted, 2026-09-26. The founder asked for it, once they had walked the website a second time. That a visit is a kind of search of its own in the service, what it is ranked by where nothing is said, and what the reader takes for one were set in the building, and are the founder's to overturn: the last section names the one place that holds each. It follows [0002](0002-deterministic-core.md), [0010](0010-one-contract-one-synthetic-release.md) and [0021](0021-a-price-is-shown-as-the-publisher-gives-it.md), and changes what none of them says of a search to rent or to buy.

## Context

- Burro was built for a person who is choosing where to live. A search said one of two things of what it was for: a home to rent, or a home to buy. The contract's word for it is `tenure`. What a budget is held against, which kinds of home may be named, the usual settings a search starts from and what a result says of cost all turn on it.
- The founder walked the website the first time, and wrote what the product is to say of itself: "The overall message of the app/product is to 'Find your area' weathe rbuying, renting, or just visitin , Burro will help you find a area to call your own." The first page has said so since ([0035](0035-the-search-page-is-one-box-and-the-look-gives-way-to-the-answer.md), as amended). A search could still be to rent or to buy and nothing else, so the first page promised a visitor what no search could be.
- The founder walked it a second time, and wrote: "Add a visiting option under renting or buying, again, this should accomodate people who are looking where to get a hotel etc. Visiting should remove some of the price and bedroom fields, we are just finding a location where they might want to book a hotel."
- A release holds what homes sell for and what they let for. It holds nothing of what a night costs anywhere, and the licence registry holds no source of it. Missing data is never filled in (rule 7), and a figure of one thing is never shown as a figure of another.

## Decision

**A search is of one of three kinds: to rent, to buy, or to visit. A visit holds no budget, no number of bedrooms and no kind of home, and what homes cost is no part of how its areas are ranked.**

| Matter | What is so |
|---|---|
| The value | `tenure` gains a third value, `visit`. Its name to a visitor is "Visiting". It is a kind of search of its own in the service, and no setting of the website alone |
| What a visit holds | Everything a search holds but a budget and a home: the places a person needs to reach, with how long each journey may take and by what means, what they want around them and how much each thing counts, and any area they ruled in or out |
| What it does not hold | An amount, whether the amount is a firm limit, how much a budget counts, a number of bedrooms, and a kind of home. The record of a search holds a budget, and a client reads it, so a visit holds a budget that is empty, `NO_BUDGET`, and the shape of a search is as it was. A search that says it is a visit and holds any other budget is no search the service reads |
| An edit that would give it one | It is turned away, and says why, and the search is left as it was. A kind of home is not for a visit (`segment_not_for_tenure`). An amount, whether it is firm, and how much a budget counts would each be held against what a stay costs, which no release holds for any area, so each is turned away as what is not in the data (`not_in_release`). It is never applied in silence, and never dropped in silence |
| In which words it is turned away | In words both clients already have. No reason was added to the list of reasons, because the website and the app each hold a sentence for every reason, and would have had none for a new one. So an amount on a visit is turned away in the sentence for what is not in the data, which speaks of figures to rank areas by, and says nothing of a visit |
| How a visit is ranked | By everything else, as any search is: journeys, vibes and measures, each by how much it counts. The release is asked for no cost. No area is left out for what homes cost there, and none stands higher or lower for it |
| What is said of an area | What is said of any area, but of cost: no reason and no trade-off of a visit speaks of what a home costs, and the facts of a visit hold no cost and no budget |
| Where nothing is said | A visit starts from the usual settings of a visitor: what somebody who is choosing where to stay for a few nights is likely to mind. Being able to get about, places to eat and drink and to go out, and something to walk to. The table below has them. They give way to what a person asks for, as the usual settings of a renter and of a buyer do |
| A search that becomes a visit | It drops the budget and the home, and keeps everything else that was asked for |
| A measure of what homes sold for | It is a measure as any other is, to the service: a visit that names one has it weighed, and cost is otherwise no part of how a visit is ranked. The website offers no such measure to a visit, and takes off any that counts as "Visiting" is chosen: what homes sold for, and how much that rose over five years and over ten. It keeps what describes a street and no purchase, as homes in the higher council tax bands do |
| A visit that becomes a search for a home | It takes the usual budget of that kind, with no amount, and keeps everything else |
| What a release must hold | Nothing more. A release that holds no cost turns away a budget, and serves a visit whole |
| The reader of sentences | A sentence that plainly says a person is visiting is read as a visit, and so is one that names a hotel or another place to stay. The words for a visit are closed lists of core's, as every word the reader knows is. A place that is visited, as a person's mother is, makes no search a visit: it is a place to reach. A price by the night is not read as a budget: Burro holds no price of a stay, and says so in the words the service had for what a place charges. A sentence that holds one is not plain, so its visit is offered and carries no guess. An amount that is typed into a visit with nothing that says what it is of is not held, and an amount by the month is a rent, which makes the search one to rent. How long a stay is, as "for a weekend", is heard and nothing is made of it. The name of the city is read as what is visited after a word for a visit, and nowhere else. In a sentence that is not plain a visit is offered, as renting and buying are |
| The website | A third choice stands beside "Renting" and "Buying": "Visiting". With it chosen nothing of a price, of bedrooms or of a kind of home is drawn, in any group of the settings, and what was set of them is not sent. A chip says "Visiting", and no chip of a budget or of a home is drawn ([0035](0035-the-search-page-is-one-box-and-the-look-gives-way-to-the-answer.md), as amended) |
| The iPhone app | It offers renting and buying, as it did. Where an answer of the service says that a search is a visit, the app shows it without a budget and without a home |

**The usual settings of a visit**, which are `_VISITOR_WEIGHTS` in `packages/core/src/burro_core/spec.py`. They are a judgement made for the founder, and that table is the one place that holds them.

| Measure | Counts for, of 1 | Once a person has asked for anything |
|---|---|---|
| The walk to the nearest station | 0.50 | 0.10 |
| Lines within a walk | 0.30 | 0.05 |
| Places to eat and drink, for each 1,000 homes | 0.30 | 0.05 |
| Pubs and bars, for each 1,000 homes | 0.30 | 0.05 |
| Cultural venues, for each 1,000 homes | 0.30 | 0.05 |
| The nearest park | 0.30 | 0.05 |

Getting about leads, as it does for a renter. Places are counted for each 1,000 homes, because a count of them is shown and never ranked on. Noise and the air are left out: they are what a person lives with, and a visitor stays a few nights. So is the town centre, which the places that stand in one already speak for. Nothing that describes who lives somewhere is among them, and no recorded crime.

**They are six, and one alone stands at 0.40 or more, so that a visitor's one place to reach outweighs all that nobody said.** Once a person has asked for anything the usual settings give way to a quarter, which is 0.35 in all, as a renter's do. A visit has no budget to stand beside a journey, so a journey stands alone there, at 0.40. A seventh measure, or a second at 0.40, would bring what nobody said level with the one place a visitor named.

What was weighed, and put aside:

| Way | Why not |
|---|---|
| A visit as a search to rent, with its budget hidden by the website | The service would go on holding a usual budget and a kind of home for it. A sentence that says "a hotel" could not be read as one, a shared link would open as a search to rent, and the app would show a budget that the website hid |
| A budget for a visit, held against what homes let for | A rent by the month says nothing of a night in a hotel. It would be a figure of one thing shown as a figure of another |
| A price of a night, from a source of its own | None is registered, and none was looked for. It is a new source, and asks the licence registry first (rule 1) |
| Hotels on the map, or a link to where one is booked | The data names no hotel. Burro ranks areas, and shows nothing to book or to buy |
| The usual settings of a renter, for a visit | They weigh the air and the noise near a home, which a person lives with, and leave out what a visitor came for |

## Consequences

- **The contract is at version 3.** `Tenure` has three values, and `defaults` of route 11 holds what a visit starts from, `visit`, which is required: that one record is what moved the version. The types of the website and the models of the app were made again from it, and answers of a visit are recorded among the answers both are tested on. The engine is 1.17.0: it knows a third kind of search, and moves no arithmetic and no result of a search to rent or to buy. Every search to rent or to buy has the hash it had.
- **What the first page says is now so.** A person who is just visiting can search as one.
- **A visitor may be of any age**, which a person who rents or buys seldom is. [The page on children](../legal/access-by-children.md) said so when the first page came to name a visitor, and the weighing there is the founder's.
- **The legal drafts say that Burro helps a person decide where to live.** What it is for is wider now. [The terms](../legal/terms-of-use.md), section 1, and [the page on children](../legal/access-by-children.md), section 6, are the founder's to word.
- **Nobody has asked a visitor what they mind.** The usual settings of a visit are a first judgement, as those of a renter and of a buyer were.
- **A visit that comes of a sentence or of a shared link may hold a measure of what homes sold for**, and the settings of the website then offer no switch to take it off by: its chip does. Whether the service turns such a measure away for a visit, as it does a budget, is the founder's to say.
- **What is said as a search becomes a visit was written for renting and buying.** Where a budget goes because the kind of search changed, the page says that what can be paid in rent is not what can be paid to buy, and that a new one can be typed. Neither is so of a visit. The words are the website's, and are still to be written for a visit: seen in a browser on 2026-09-26, a search to rent that became a visit was told both.
- **What people are told is sent to a model names two kinds of search.** Where the service is set to send the search with the words, its notice says "whether you rent or buy". It is the service's sentence, in `services/api/src/burro_api/providers/terms.py`, and [the design of the models](../design/models.md) quotes it word for word, held by a test. The two change together, in one change.
- **A visit is ranked on what a release holds.** A build of London works out five of the six measures of the table above. It works out no count of the lines within a walk, which the usual settings of a renter and of a buyer name too, so no area has a figure for it, and a usual setting that has no figure moves no area ([0024](0024-an-area-with-no-figure-for-what-was-asked-stands-below.md)). It holds no journey time, so a journey of a visit is estimated from distance, and says so, as any journey is ([0027](0027-a-journey-is-estimated-from-distance-until-a-timetable-is-held.md)).
- **Nothing of the rules on who lives somewhere, on recorded crime or on a verdict of a place is changed.** A visit is a search, and every rule of a search holds of it.

## What would change it

| If | Then |
|---|---|
| The founder wants a sentence of its own where a visit is given a budget | It is a new reason, which is a change to the contract, and a line in each client |
| The founder wants other usual settings for a visit | The one table, `_VISITOR_WEIGHTS`. `test_what_a_visitor_says_outweighs_the_usual_settings` holds that one place to reach outweighs them once they have given way |
| A source of what a stay costs is registered, with a licence that allows it | It is a new decision whether a visit may hold a budget. A release would carry the cost, and the contract a kind of cost that is no rent and no price |
| A word that says a visit is read where none was meant, or the other way | The words are core's, in one list. A case is written first, and the reader is scored again |
| The founder wants a visit to be of so many nights, or of a season | The search gains a part, which is a change to the contract. Nothing a release holds differs by night or by season |
