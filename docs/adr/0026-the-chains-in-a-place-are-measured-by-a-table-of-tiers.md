# 0026. The chains of grocers, gyms and coffee in a place are measured, by a table of tiers that is the founder's

Status: accepted, 2026-09-24. The founder decided it. The table of tiers is the founder's to adjust. Four points are theirs to confirm: the last section says which.

## Context

Burro counted the places to eat and drink and the cultural venues within reach of home, and said nothing of which shops they are. A word for a smart area, "affluent", had two readings, both of the place: the polished end of Gritty, and what homes sell for ([0013](0013-vibes-are-the-centre.md), [0021](0021-a-price-is-shown-as-the-publisher-gives-it.md)). Neither says what a person sees on the high street.

The file of places that Burro reads for cultural venues, `overture-places`, gives a place a brand where its publisher has matched it to a chain. It gives the name of the chain, and for some the id an encyclopaedia gives it. No name of a place, no address and no telephone is read to find one.

## Decision

The founder decided, on 2026-09-24, in these words, with the spelling put right:

> We need to include these brands to give us an idea of "quality" and socioeconomic factors.

And of the table below:

> Yes, we want exactly this and a count of distance etc.

And of how it is built:

> Let's not over-engineer or over-complicate.

**The table of tiers.** It is the founder's judgement of each chain: what it charges, and how it presents itself.

| | Premium | Mid-range | Value |
|---|---|---|---|
| Grocers | Waitrose, M&S, Whole Foods | Sainsbury's, Tesco, Co-op | Asda, Aldi, Lidl, Iceland |
| Gyms | Equinox, Third Space, Barry's | Virgin Active, Nuffield, Gymbox | PureGym, The Gym Group |
| Coffee | Gail's, Ole & Steen | Pret, Nero, Starbucks | Greggs |

**Five chains were added beside them**, each as mid-range, and each a first guess that the founder has not seen: Morrisons among the grocers, David Lloyd and Anytime Fitness among the gyms, and Costa and Blank Street among the coffee. The file of the table marks each as added. One that was thought of was not added: Planet Organic, of which the file holds no place.

**The table is one file of data, and no code.** It is `packages/pipeline/src/burro_pipeline/derive/brand_tiers.toml`. A row holds the chain, its kind, its tier, whether the founder gave it, and how the file of places writes it. To move a chain to another tier, or to add one, a person changes that file. Core names the kinds, the tiers and the chains, so that a person can ask for one, and never says which chain is of which tier.

**What is measured**, for each of London's areas, from where its homes stand:

| What | How |
|---|---|
| The places of each tier | For grocers, for gyms and for coffee, the places of chains of each tier within 800 m of home in a straight line, as the mean over the area's homes |
| The nearest of each tier | How far the nearest of them is, where one is within 2,000 m |
| The nearest of each chain | How far the nearest place of one chain is, where one is within 2,000 m. It is what an area's page says by name: a Waitrose, so many metres |
| The mix | Of the places of a tier within 800 m, the share that are premium, with a mid-range one counted as half. **It is what is ranked on** |
| Independent places | Of the places to eat and drink within 800 m, the share that belong to no chain. It is a part of Food and drink, at 40 in 100, and of Village feel, at 25 in 100, as each recipe already said |

**What a person may ask.**

| The words | What is offered |
|---|---|
| "Affluent", "posh", "upmarket" and their kin | Three readings, each of the place, and the person chooses: the mix of brands, more premium, which is first; the polished end of Gritty; and homes that sell for more. Each says "Burro measures places, not the people in them" |
| "Cheap and cheerful", "unpretentious", "down to earth" | The other end of the mix, and nothing else |
| The name of a chain: "near a Waitrose", "a Gail's nearby" | The distance to the nearest place of that chain. It is offered, and never applied, because the file misses some shops |

Nothing weighs any of these by default, none stands in a vibe, and no likeness is counted on one. The catalogue is version 13.

## How this sits with ranking places and never residents

[Decision 0006](0006-rank-places-not-residents.md) holds that Burro ranks places and never residents. Every measure here counts shops. None counts a person, and none is told from who lives anywhere.

The founder's aim names socioeconomic factors, so the mix is wanted because it follows how well off a place is. That makes it a stand-in by design, and 0006 asks for a row of the proxy audit before such a measure is served. The row is in [the page on brands](../research/data/brands.md), section 8, and was written before any release held the mix. What it found: across London's areas the mix follows what homes sell for, at a rank correlation of 0.48. What it could not find is whether the mix follows who lives in an area, because no file is registered for the audit. **Amended, 2026-09-25:** the founder dropped the proxy audit that day ([0006](0006-rank-places-not-residents.md), as amended). The row stays as a record of what was measured, and holds nothing back.

One name was shortened. Core holds no name of a measure with a word that may be said of residents, and the full name of one chain of gyms holds such a word. It is said "Nuffield".

## Consequences

- **An area's page names chains.** A chain's name is no secret, and the table names each. The name of a shop that belongs to no chain is never read, and is in no file.
- **The file does not hold every shop.** A brand is given only to places that two of the file's sources gave. Of the founder's 24 chains, the file holds no place of two, Third Space and Gymbox, and a handful of three more. So the premium tier of gyms is nearly empty, and no area can be said to be near a Third Space. The page on brands has the count of each.
- **The mix rests on few places in the outer boroughs.** About one area in six has fewer than two places of a tier within reach of a typical home, so one shop opening or closing moves its mix a long way. Nothing sets a least number of places yet.
- **Independent places are what the file says, and not what the word suggests.** The share is highest where chains have not gone, which is often where rents are low. It is lowest in some of the smartest parts of London, where every other place is a chain. A person who asks for "independent cafes" may not mean that.
- **A word for a smart area is offered three ways.** The list under a sentence is one longer.
- **Food and drink can be placed, and Village feel holds enough of its recipe to be.** Each waited on independent places. Whether Village feel finds villages is a separate question, which its own two measures of a town centre still wait on. **Amended, 2026-09-24:** it does not, so it places an area only where one of those two has a figure, and no build places an area on it ([ADR 0013](0013-vibes-are-the-centre.md), as amended).

## What would change it

| If | Then |
|---|---|
| The founder moves a chain to another tier, or adds or takes off a chain | One row of `brand_tiers.toml` changes, and a chain that is new to core gains an id. The measures are built again. Since 2026-09-25 the same is done at the panel of the review desk, as a line of the file of changes that a build lays over the table ([0029](0029-a-change-reaches-a-release-through-a-file-of-changes.md)): the file of the table is then what a build starts from |
| The founder does not want one of the five that were added | Its row comes off the table, and its id stays in core and is carried by no release |
| A mid-range place should count for more or less than half | One number in `brands_nearby.py`, and the method of the mix gains a version |
| The mix should not be said where few places stand behind it | The measure is left out for an area with fewer than a set number within reach, and says so |
| Independent places, as measured, do not belong in a vibe | The recipe of Food and drink or of Village feel changes, which is a change of the catalogue |
| A second source of shops is registered | The chains the file misses can be counted. Until then an area's page says what the file holds, and that it misses some |
| The audit finds that the mix follows who lives in an area, at 0.5 or more | The mix is taken out of what is offered for a word for a smart area, or is shown and no longer ranked on. **Dropped on 2026-09-25**, with the proxy audit: no audit is run, so none finds it |

## For the founder to confirm

1. The five chains that were added, and that each is mid-range.
2. That a mid-range place counts as half a premium one in the mix.
3. That the mix is said for every area with any place of a tier within reach, however few.
4. That independent places, as the file can tell them, stay a part of Food and drink and of Village feel.
