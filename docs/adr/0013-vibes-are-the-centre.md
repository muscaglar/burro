# 0013. Vibes are the centre, and gritty is built two ways

Status: accepted, 2026-09-23. Builds on [0002](0002-deterministic-core.md), [0006](0006-rank-places-not-residents.md) and [0010](0010-one-contract-one-synthetic-release.md). Amended on 2026-09-24: the founder decided which way gritty is built for London, which was the first of five points to decide, and then its name and its recipe. Three are still for the founder to decide. Amended on 2026-09-25: a second try at Village feel did not clear the founder's bar, and the founder accepts that pubs and bars are counted from the file of places. Amended again on 2026-09-25: the founder chose to serve Village feel as a rough guide, though no try had reached the bar.

## Context

People ask for a kind of place: leafy, villagey, lively, gritty. Burro answered with 23 measures and 12 tags, and a person met a hundred controls before they met a place. The tags were made one at a time. Two were one measure under another name, one tag could be decided by a single source, and a tag was said as a percentage of areas, which reads as a score of the place.

"Gritty" is the hard one. Part of what people mean by it is land use: works, depots, railway arches. Part is how clean or run down a street is, which no open data measures. And part is recorded crime, which [0006](0006-rank-places-not-residents.md) keeps out of every tag.

## Decision

**A vibe is a recipe over measured things, and it is what the product is asked for.** A release carried eleven, and carries twelve since Gritty became one vibe beside Works and warehouses. Each has a plain meaning, a recipe in hundredths, and a list of what it cannot see, which begins the same for every one: "One street or one home. An area is many streets."

- A recipe is checked when the catalogue is made, in code. Its hundredths sum to 100. No part carries 60 or more, so no one source can decide a vibe. No part is a thing that is weighed only on request.
- A vibe is a **scale** with two named ends, of which a person may ask for either, or it has **one way**. Going out runs from Calm to Buzzy.
- A vibe is **said as a band**, one of five, among the areas compared. It is never said as a percentage, a score or a rank. An area that is mixed is said as a range. An area that cannot be placed is said to be that, and is never drawn in the middle. Every sentence ends: "The recipe is Burro's own. The weights are a judgement."
- The mid-rank percentile is still what a vibe is ranked on. Ranking stays a pure function of the spec and the release.
- Seven tags are retired, and their ids are never reused. Their words weigh what took their place.

**Gritty is built two ways, behind one setting of the release.** `manifest.gritty_variant` is `a` or `b`.

| | `a`: Works and warehouses | `b`: Street character, which is now Gritty |
|---|---|---|
| Shape | One way | A scale, from Polished to Gritty |
| Made of | Land used for industry, storage, depots and yards | Industrial land, main roads, transport noise, homes close together, recorded criminal damage and recorded anti-social behaviour |
| Recorded incidents | None | 35 of 100 hundredths |
| May be in | Any release | Any release, since 2026-09-24. Until then a synthetic release only: `parse_release` refused any other, by the rule `gritty_b_is_synthetic`, which is taken out |

Neither holds a figure about who lives somewhere: no income, employment, health or education. The committed synthetic release is `b`, so that the founder can see it.

**Amended, 2026-09-24: gritty is one vibe, and a release of London carries it as `b`.** The founder decided that gritty combines both ways: works and warehouses, recorded criminal damage, recorded anti-social behaviour, main roads, noise and density, with every other measure of the place that is held. It is read as data about the place: nothing about who lives there is in it. It is an opinion, and the recipe says so: the weights are a judgement that a person may review and adjust. To type "gritty" is to ask for recorded crime by name. [0006](0006-rank-places-not-residents.md) is amended with it. What follows:

- `parse_release` no longer refuses `b` on a release that is not made up, and a build of London carries `b`.
- Recorded crime still counts only when a person asks for it by name: an edit that is only inferred never weighs the vibe, and every choice that would weigh it says on its face that it counts recorded crime. It is never labelled safe or unsafe.
- An area has a band on gritty only where 60 in 100 of its recipe is measured. A build holds main roads, noise and density, which are 45. So no area of London has a band until the land use table or recorded crime is held, and a wish for it is said to be missing and is never filled in.
- The recipe is as it was built: what "every other measure of the place that is held" adds to it, and with what weight, is not decided here. Nor is the name: the scale is still called Street character, from Polished to Gritty. Both were decided later the same day: see the next amendment.

**Amended, 2026-09-24: Gritty has its name and its recipe, and Works and warehouses stays a vibe of its own.** The founder saw the recipe, and then what it did to London, and decided each.

| Part | Hundredths |
|---|---|
| Recorded criminal damage | 30 |
| Works and warehouses: land used for industry, and land used for storage and warehousing | 30 |
| Recorded anti-social behaviour | 15 |
| Main roads | 15 |
| Transport noise | 10 |

- **The name is Gritty.** The scale runs from Polished to Gritty, under the id `street_character`, which it keeps: an id is never renamed. It answers to the name it had, "street character", which names no end.
- **What is recorded is 45 in 100 of it, and works and warehouses 30.** The recipe first shown to the founder held homes per hectare and nitrogen dioxide, at 10 each. They were taken out: with main roads and noise they were 45 in 100, each says central and built up, and between them they put most of a smart central district in the two grittiest bands. So the recipe holds what says gritty of a place, and not every measure that is held.
- **Works and warehouses is 30 as two parts of 15**, land used for industry and land used for storage and warehousing, because no part may be a vibe and each is a measure of its own. That split is the builder's, and is the founder's to change.
- **Works and warehouses stayed a vibe of its own**, with its recipe as it was, until the amendment below made it a part of Gritty alone. A release that carried Gritty carried twelve vibes, and said `b` in `manifest.gritty_variant`. A release that holds no recorded crime carries eleven, every vibe but Gritty, and says `a`: there the word "gritty" is still read as Works and warehouses, as assumed. No release that is served is one.
- **To type "gritty" is to ask for recorded crime by name**, and so is to press a choice that says it counts it. The chip of a search that holds Gritty says "counts recorded crime", and so does its card, before anything on the card can be pressed.
- **The rule stands for everything else.** Recorded crime counts only when a person asks for it by name. "Safe" names no crime: it is never applied, recorded crime is offered by its name, and the person is told that Burro cannot say how safe a place is. "Edgy", "raw", "rough", "affluent" and "posh" are only read into Gritty, and are offered and never applied. No other recipe holds recorded crime, and a result never shows Gritty where it was not asked for.
- **On what was held that day a release of London placed no area on it.** Main roads and transport noise are 25 in 100. Land use brings it to 55, and recorded crime to 70 without land use. An area has a band at 60.
- **The weights are a first opinion.** A person reviews and adjusts them.

**Amended, 2026-09-24: what is said of the place leads over a journey and a budget.** A journey weighed 1.00 and a budget 0.80, against 0.50 for each thing said of the place, so one journey and one budget outweighed three things said. For a person who asked for leafy and quiet, named a workplace and gave a rent, the second result was the works, in band 2 of 5 for Leafy. The founder decided that what is said of the place leads. A journey now weighs 0.40 and a budget 0.30 until a person moves them: each thing said of the place weighs more than either, and two things said outweigh the two together. A firm limit is a filter and no weight, so it still leaves out what is over it. Three other pairs were tried on the made-up city. At 0.50 and 0.40 an area in the lowest band for Quiet streets was still among the first five for that search. At 0.25 and 0.20 the first five were as good on the place as at 0.40 and 0.30, and a journey and a budget together weighed no more than all that a buyer left unsaid. Raising what a mention is worth was not taken: a mention would stand at the most a thing can weigh, and "really leafy" could add nothing. What gives way is the budget: an area over a flexible budget, or over a flexible limit on a journey, can now stand high where it does well on the place, and its card says what it gives up.

**Amended, 2026-09-24: Going out counts no pub while the pubs are held back.** Pubs and bars were 35 in 100 of Going out. A check of the food register found that pubs alone follow how a council fills the register in as much as they follow pubs, so the measure is held back from every release. The founder decided that Going out is made of the other three parts until a second source confirms the pubs. The recipe is places to eat and drink 45, a high street within reach 30 and culture venues 25: the shares the three stood in, to the nearest five. The places to eat and drink are those for each 1,000 homes, which a wish for them is ranked on, and not the count, which says little more than that an area is dense and central. No one part gives a band, and any two do. A build of London holds the first part alone, 45 in 100, so it places no area on Going out: it waits on high streets and on culture venues, and either gives it a band. The recipe of Food and drink is as it was, and still holds the count at 40 in 100: whether it should hold the places for each 1,000 homes is the founder's to say.

**Amended, 2026-09-24: pubs and bars are counted from the file of places, and are in Going out again.** The founder asked for cafes and gyms to be used, and had decided that the pubs join Going out when a second source confirms them. The file of places is a second source, so the two were held against each other, borough by borough. The register gives a point to 3,562 pubs, bars and nightclubs in London, and the file holds 6,559 pubs and bars. Across the areas the two counts stand in one order at 0.90. The file did not confirm the register: under the council that lists 4 in 100 of its places to eat and drink as a pub, the register gives a point to 147 and the file holds 834, and one in three of the file's pubs and bars stands beside a place the register lists as a place to eat. So the file stands in the register's place, and the register's pubs alone are carried by no release. The file has a fault of its own, which every figure of pubs says: it is thin toward the edge of London, where in three boroughs under six in ten of the register's pubs have a pub or a bar of the file within 200 metres. What follows:

- **Going out is pubs and bars 35, places to eat and drink 30, a town centre within reach 20 and culture venues 15,** which are the shares it had before the pubs were taken out. While they were out it was 45, 30 and 25. Each count of venues is the figure for each 1,000 homes, and the town centre is a distance, read from its near end.
- **Quiet streets is as it was:** main roads 40, homes near a cluster of pubs and bars 30, transport noise 30. The part was named for clusters of evening venues and no build measured it. It is measured now, and is named for what is counted: the share of homes with three or more pubs or bars within 150 metres, in a straight line. The file cannot say how late a place is open, so no name says late, and a nightclub is not counted.
- **Cafes, gyms and pubs are measures a person may ask for by name,** each shown as a count within 800 metres of home and ranked on for each 1,000 homes, as places to eat and cultural venues are. Cafes and gyms are in no vibe: nobody asked for one, and a recipe is the founder's to change.
- That the file stands in the register's place was a call made for the founder: the founder's decision was that a second source confirms the pubs, and this one did not. **The founder accepted it on 2026-09-25:** see the amendment of that day, below. Which category of the file is which kind, that three are a cluster, and that records within 25 metres are one place are calls made for the founder still, and theirs to overturn.

**Amended, 2026-09-24: three vibes are named for what a person would call them.** The founder chose the names. Pace is "Going out", and its ends are still Calm and Buzzy. Homes is "Houses or flats". Built age is "Age of buildings". Each had the name of its recipe, and nobody asks for a place by one. No id, end or recipe moved, so a search that was saved ranks as it did. The reader answers to each new name and to the old, and the name of a scale still names no end: it is offered with both and never applied. "Homes" alone is what is being looked for, and is no name of a vibe to the reader.

**Amended, 2026-09-24: Works and warehouses is a part of Gritty, and no vibe of its own beside it.** Its figures are right at the top and wrong as five bands: about a third of London's areas hold no such land and tie in the lowest band, and an area with a little of each kind of land stands above an area with much of one. So a release that carries Gritty carries eleven vibes, and serves none of the name Works and warehouses. The words for it, "warehouses", "industrial", are offered as Gritty. A release that holds no recorded crime still carries it in Gritty's place, and says `a`. Three more things follow the decisions of that day. Food and drink ranks on places for each 1,000 homes, as Going out does, and Going out on cultural venues for each 1,000 homes: no recipe holds a count that is shown and never ranked on. Going out and Everyday on foot weigh the distance to a town centre, in a straight line, where they weighed a share of homes near a high street. Leafy is served on its recipe, and says that a wood that is a public park is counted twice. With the police's files and the table of land use, a build of London holds the whole of Gritty's recipe and places every area. Each was a call made for the founder, and each is theirs to overturn.

**Nothing about who lives somewhere is built.** A feature says what it describes: a place, its buildings, or what was recorded there. There is no fourth word.

**Likeness is counted on measured things, and never on a vibe, a nuisance, recorded crime, cost or a journey.** A feature says for itself whether likeness may use it, and code refuses a nuisance whatever the flag says.

**The portrait of an area is built with no spec**, so it is the same for everyone.

The contract, sections 2 to 7, holds the records and the rules.

**Amended, 2026-09-24: Village feel places an area only where something of its town centre has a figure.** The founder decided that Village feel is served only if a second try at it reads as villages. No second try has been made. Once independent places were measured, a build of London held 60 in 100 of its recipe, which is enough for a band, and none of it was the size or the shape of a town centre: it found inner London's old streets and no villages. So core places an area on it only where one of those two measures has a figure, whatever else has. No build carries either yet, so no build places an area on it, and nothing else of the catalogue moved. [The contract](../design/contract.md), section 3.2, has the rule.

**Amended, 2026-09-25: a second try was made, and Village feel stays held off.** The founder set the bar on 2026-09-24: at least 30 of the 50 areas a recipe puts highest read as villages. The first try reached 8. The second read the file of high street boundaries for the first time, and measured how much of the high street nearest a home lies inside a conservation area. Three recipes were worked out for every area of London, and each fifty was read three times, by the name of the nearest high street and the borough alone. No reading was made by a person who knows the places.

| Recipe | Read as villages, of its fifty highest |
|---|---|
| The first try | 8 |
| A: a small high street 25, the high street in a conservation area 35, homes built before 1919 20, conservation cover 20 | 10, 11 and 9 |
| B: as A, and the conservation area counts only where the high street is under 20 hectares | 8, 9 and 7 |
| C: the high street in a conservation area 45, homes per hectare read from the low end 30, homes built before 1919 15, conservation cover 10 | 24, 24 and 23 |

- **None clears the bar, so nothing changed in core.** The recipe of Village feel is as it was, `PLACED_ONLY_WITH` names the size and the shape of a town centre as it did, and no build places an area on the vibe. A wish for it is turned away as it was.
- **C is the best that was found.** It puts the seven places the founder named as villages among its first 37 of 925. A search of 65,000 simple recipes of the figures that are held found none that reached 30.
- **The measure is built and joins no build.** Core holds no feature for it. It is worked out by `derive/highstreet_conserved.py`, and a test fails when core gains the feature.
- **What would mend it** is in [the page on high streets](../research/data/high-streets.md), section 8: a person who knows the places reads the fifty, and a figure that tells a village street from a trunk road.
- **The founder may overrule the readings, or the bar.** To serve C is one change to core: a feature for the measure, the recipe, and nothing in `PLACED_ONLY_WITH`, since no area has 60 in 100 of C without the high street.

**Amended, 2026-09-25: Village feel is served, and says that it is less sure.** The founder was shown that no try had reached the bar, and asked: "4. Can we include village anyhow? With less certainty perhaps?" So it is served, as a rough guide. What is above is as it was written, and is the history of how it came to this.

The bar of 2026-09-24 was not reached. It was that at least 30 of the 50 areas a recipe puts highest read as villages. Three tries were made.

| Try | What its recipe counts, in 100 | Read as villages, of its fifty highest |
|---|---|---|
| The first | Independent places 25, a small centre 20, a compact centre 20, homes built before 1919 20, conservation cover 15. A build held 60 of it, and nothing of a town centre | 8 |
| The second, which is recipe C above | The high street in a conservation area 45, homes per hectare read from the low end 30, homes built before 1919 15, conservation cover 10 | 24, 24 and 23, by three readers who read the name of a high street and a borough alone. 27 once the founder had read thirteen of the fifty, and their reading stood in place of the readers' |
| The third | As the second, with the traffic counted on the nearest high street read from the low end: 40, 25, 20, 10 and 5 | 25, by the founder's reading where the founder had read, and the readers' elsewhere |

- **What is served is the recipe of the second try, with no share changed:** 45, 30, 15 and 10. It has no part for a small or a compact centre, for independent places, for traffic, or for homes per hectare of the land that is no park.
- **The measure of the high street joins a build.** Core names it `highstreet_conserved`, the catalogue is at version 14, and no likeness between areas counts it. The parts of a recipe that rest on the conservation areas come to under 60 in 100 between them, so that their publisher's file never places an area alone: they are 55 of Village feel.
- **No vibe is held off.** `PLACED_ONLY_WITH` names none. The rule stands, for any vibe that is held off in future, and a test holds it on a vibe that is not. Village feel needs no such rule: without its high street an area holds 55 in 100 of the recipe, which is under what a band needs.
- **A vibe says how sure it is.** It is one field, `sureness`, with two values: `as_the_rest`, and `rough_guide`. It is no number and no word of praise or blame, and no client works it out. A vibe that does not say is as sure as the rest, which is what a client assumes of a release that was written before. The field is core's: a release that says otherwise of any vibe is refused, and no change at the panel moves it. Village feel is the one rough guide.
- **A person is told, in sight and behind no press.** One label, "Rough guide", and one sentence: "Of the areas it puts highest, about half read as villages to people, and it takes some busy main roads and some grand inner streets for villages." Core holds both, and the website, the app and the panel draw them: on the chip of a search, on a result, beside the band on the page of an area, in its offer, on the page of vibes, and at the panel. The sentence holds no figure that a build could make false, and names no place.
- **It is never taken without a press of its own.** The rules apply it from no word, its own name among them, and offer it with its label and its sentence. The one press that adds what needs no choice never takes it. A model's guess of it is no guess. The note under a word for character names it among the ways that are offered, with its label.
- **It is used to work out nothing else.** No likeness counts it. It is on a result only where the person asked for it, so no explanation gives it as a reason unless they did. No portrait says that an area has most or least of it.
- **What would make it as sure as the rest** is what the bar asked: 30 of the fifty, read by a person who knows the places. That is a decision of its own, and one line of core.

**Amended, 2026-09-25: the founder accepts the file of places for pubs and bars.** The founder had decided that the pubs join Going out when a second source confirms the food register. The file of places is a second source, and it did not confirm the register: it was taken in the register's place, as a call made for the founder. It was put to the founder as the fifth of a list of questions, and these are their words:

> (5) Accept the venue file

So pubs and bars are counted from the file of places and from nothing else, as they are built, and are 35 in 100 of Going out. The register's pubs alone are carried by no release. No code changed. What the file cannot see is said beside every figure of pubs, as it was: it holds fewer pubs toward the edge of London, and no person has looked at a sample of its records.

## Consequences

- A search starts from seven words, and the settings are grouped by four families. The hundred controls are one press further away.
- The release's schema and the catalogue are at version 2. A release of version 1 is refused.
- Three recipes run short on the data there is today, because four measures have no cleared source: private outdoor space, kinds of food, the walk to a GP and the walk to a pharmacy.
- "Gritty" and "polished" are words the verifier refuses in any sentence, but as the name of an end of the scale.
- In variant `a` the word "gritty" is read as land use, and the person is told that Burro has no measure of how clean a street is.
- In variant `b` the words "edgy", "raw", "smart" and "well kept" were read into a vibe that holds recorded incidents, and the label of the scale was read as a wish for its Gritty end. **Amended, 2026-09-23:** crime counts only when a person asks for it by name. The reducer now holds a vibe whose recipe holds recorded crime to the rule it holds a crime feature to: an edit that is only inferred never weighs it. The reader applies such a vibe from the name of an end alone, "gritty" or "polished". From any other word, and from the name of the scale, it applies nothing and offers the scale, and the offer says that it counts recorded criminal damage and anti-social behaviour. Whether the name of an end is asking for crime by name is the founder's to judge, with the names themselves.
- Every sentence about a vibe ended in the line that its recipe is a judgement. **Amended, 2026-09-24:** in an explanation, which is the reason and the trade-off of a result, a vibe is said in short: where the area sits, and what that rests on where it is part of a recipe. The sentence ran to thirty words, half of them the same on every result. The line about judgement and the date of the parts stay in the fact the sentence cites, and the website shows both with the source, one press away. The full statement still ends in the line, and stands on the page of an area and on the page of every vibe. Whether one press away is near enough is the founder's to judge (slice-1.md, section 10).

## To decide

1. **Which way gritty is built for London.** Decided on 2026-09-24: one vibe that holds recorded incidents, named Gritty, with the recipe of the second amendment above.
2. **Anti-social behaviour as a part.** Decided on 2026-09-24 with the recipe: it is 15 of the 100 hundredths of Gritty. It is recorded where it is reported, and the caveat says so wherever it is counted.
3. **The names of the ends.** Polished and Gritty, Calm and Buzzy, Newer and Historic, Houses and Flats. The names of three vibes were decided on 2026-09-24: see the amendment above. The family of the settings that holds Going out is still called "Pace and food".
4. **The recipes.** Every weight is a judgement until the sanity set of 40 neighbourhoods exists. Gritty's was decided on 2026-09-24, as a first opinion.
5. **How a vibe is said on a result.** In short, with the line about judgement behind "Source", or in full.
