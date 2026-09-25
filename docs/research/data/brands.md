# Brands: the chains of grocers, gyms and coffee, on the real file

Written 2026-09-24. A dated snapshot, not a source of truth.

The founder decided on 2026-09-24 that the chains in a place say something of it, and gave a table of tiers ([decision record 0026](../../adr/0026-the-chains-in-a-place-are-measured-by-a-table-of-tiers.md)). This page says what the file of places holds of those chains, what was measured from it, and what the measures follow. Every figure was worked out from the part of release 2026-09-23.0 of Overture Maps Places that the list `m2-culture` takes with the brand, through its receipt.

**No figure here is of a named neighbourhood, and no name of a place was read.** A figure is of the part, of London as a whole, or of a borough. The name of a chain is no secret, and the table names each. No person has looked at a sample of the records, and nobody has reviewed this page.

Credit: Overture Maps Foundation, overturemaps.org. Records from Meta are under CDLA-Permissive-2.0 and records from AllThePlaces under CC0. No record that bears a brand is from Foursquare.

## 0. In short

| Question | Answer |
|---|---|
| Does the file say which chain a place is of | For some. Of 432,478 open places inside London, 38,122 bear a brand: about 9 in 100 |
| Who gives the brand | Two of the file's sources. No place that Foursquare or Microsoft alone gave bears one |
| How many places of the table's chains are counted | 4,857 in the part, of which 3,266 stand inside London |
| Does the file hold every chain of the founder's table | No. It holds no place of Third Space or of Gymbox, one of Ole & Steen, two gyms of Equinox and five of Whole Foods |
| How many areas have a mix | 990 of 1,002. It runs from 4 to 85 in 100, with a middle of 43 |
| What does the mix follow | What homes sell for, at 0.48. How central an area is, a little, at -0.21. How built up it is, not at all, at 0.04 |
| Would a Londoner recognise the mix | Broadly, yes. Section 5 |
| How many areas have a share of independent places | 992 of 1,002. It runs from 58 to 100 in 100, with a middle of 83 |
| Would a Londoner recognise independent places | No, not as the word is usually meant. It is highest where chains have not gone. Section 6 |
| Is the row of the proxy audit written | Yes, before any release held the mix. Section 8 |

## 1. What the part holds

| | |
|---|---|
| Rows in the part | 683,409 |
| Rows that bear a brand | 58,882, each with a name, and 22,806 of them with the id an encyclopaedia gives the chain |
| Different names of a brand | 8,704 |
| Rows inside London, by the outlines of London's LSOAs | 432,481, of which 3 have closed for good |
| Open places inside London that bear a brand | 38,122 |
| Of those, a brand of the table of tiers | 3,713, whatever kind of place it is |

Inside London, by the kind of place the file says it is:

| Kind | Open places | Bear a brand | Of a chain of the table, of this kind |
|---|---|---|---|
| A grocer: a grocery, convenience, frozen food, discount or department store | 8,744 | 3,038 | 1,667 |
| A gym: a sport or fitness facility, or a health and wellness club | 8,561 | 1,003 | 350 |
| A place to eat or drink, which is where coffee is filed | 52,050 | 7,491 | 1,296 |

**Which sources give a brand.** Of the places to eat and drink in the box round London, Meta gave 40,501, of which 7,623 bear a brand, and AllThePlaces gave 762, of which 728 do. Foursquare gave 10,188 and Microsoft 5,700, and none of theirs bears one. So for a place that only Foursquare or Microsoft gave, the file does not say whether it is of a chain.

## 2. The table of tiers, held against the file

A place counts for a chain where the file gives it the chain's brand, by the id or by the name as written, and also gives it a category of the chain's kind. Places of one chain within 25 metres of each other are one place.

| Chain | Kind | Tier | Rows in the part | Places counted | Inside London | How the file writes it |
|---|---|---|---|---|---|---|
| Waitrose | Grocer | Premium | 150 | 147 | 77 | Waitrose & Partners, Little Waitrose, Waitrose |
| M&S | Grocer | Premium | 331 | 253 | 145 | Marks and Spencer, Marks & Spencer |
| Whole Foods | Grocer | Premium | 5 | 5 | 5 | Whole Foods Market |
| Sainsbury's | Grocer | Mid-range | 502 | 471 | 382 | Sainsbury's, Sainsbury's Local, and one spelling that names a town outside London |
| Tesco | Grocer | Mid-range | 1,110 | 676 | 474 | Tesco, Tesco Express |
| Co-op | Grocer | Mid-range | 454 | 449 | 242 | Co-op, Central Co-op Food, The Co-operative Food, Southern Co-op, Coop, Co-op Daily |
| Morrisons, added | Grocer | Mid-range | 89 | 76 | 24 | Morrisons Daily, Morrisons |
| Asda | Grocer | Value | 149 | 71 | 44 | Asda, Asda Express |
| Aldi | Grocer | Value | 101 | 101 | 54 | ALDI, Aldi |
| Lidl | Grocer | Value | 135 | 132 | 88 | Lidl |
| Iceland | Grocer | Value | 154 | 147 | 108 | Iceland Foods, Iceland |
| Equinox | Gym | Premium | 6 | 2 | 2 | Equinox |
| Third Space | Gym | Premium | 0 | 0 | 0 | The file holds none |
| Barry's | Gym | Premium | 7 | 7 | 7 | Barry's |
| Virgin Active | Gym | Mid-range | 24 | 23 | 20 | Virgin Active, and two spellings that name another country |
| Nuffield | Gym | Mid-range | 60 | 48 | 32 | Three spellings, each beginning with the chain's full name |
| Gymbox | Gym | Mid-range | 0 | 0 | 0 | The file holds none |
| David Lloyd, added | Gym | Mid-range | 61 | 47 | 27 | David Lloyd Clubs UK, David Lloyd Clubs |
| Anytime Fitness, added | Gym | Mid-range | 102 | 102 | 73 | Anytime Fitness, and one spelling that names another country |
| PureGym | Gym | Value | 135 | 135 | 93 | PureGym, and one spelling that names another country |
| The Gym Group | Gym | Value | 112 | 109 | 95 | The Gym Group, and one spelling that names a town outside London |
| Gail's | Coffee | Premium | 65 | 65 | 56 | GAIL's |
| Ole & Steen | Coffee | Premium | 1 | 1 | 1 | Ole & Steen UK |
| Pret | Coffee | Mid-range | 287 | 281 | 255 | Pret A Manger |
| Nero | Coffee | Mid-range | 231 | 222 | 166 | Caffè Nero, and one misspelling |
| Starbucks | Coffee | Mid-range | 286 | 279 | 191 | Starbucks |
| Costa, added | Coffee | Mid-range | 669 | 656 | 395 | Costa Coffee, Costa, and one spelling that names another country |
| Blank Street, added | Coffee | Mid-range | 9 | 9 | 9 | Blank Street |
| Greggs | Coffee | Value | 344 | 343 | 201 | Greggs |

Inside London the places counted are, by kind and tier:

| | Premium | Mid-range | Value |
|---|---|---|---|
| Grocers | 227 | 1,122 | 294 |
| Gyms | 9 | 152 | 188 |
| Coffee | 57 | 1,016 | 201 |

**What the file does not hold.** No place of Third Space or of Gymbox bears its brand, under any spelling. Planet Organic, which was thought of as an addition, has none either, and was not added. The premium tier of gyms is nine places in all of London, so almost every area has none within reach. The file holds one Ole & Steen and 56 of Gail's, which is fewer than a person who knows the chains would expect. Nothing is filled in.

**A spelling that names somewhere else** is the publisher's own match of a London place to a brand as it is written for another country or town. The id is the chain's, and the place stands in London, so it counts. The table lists each spelling whole. The list is in `brand_tiers.toml`, and no spelling is matched by a part of it.

## 3. What is left out, and why

| Left out | Rows of the table's chains | Why |
|---|---|---|
| Not of the chain's kind | 654 | The file gives the place the chain's brand and a category of another kind: a petrol station, a bank, a pharmacy, a cafe inside a shop. Of these, 426 are Tesco's and 78 Asda's |
| Counted already | 68 | It stands within 25 metres of a place of the same chain that was counted |
| Closed for good | 0 | The file says so of three places in London, and none is of a chain of the table |

One brand is kept off the table on purpose: the vending machines of one coffee chain, which the file gives a brand of their own, 1,906 rows in the part. A machine in a petrol station is no coffee shop.

## 4. The measures

Each is worked out from the point the statistics office gives as the centre of each census output area, and joined to an area by its homes. A place is within reach at 800 metres in a straight line. The nearest is looked for as far as 2,000 metres, which is as far as the part is known to hold every place round every home.

| Measure | Areas with a figure, of 1,002 | Least, middle, most |
|---|---|---|
| The mix of brands | 990 | 4, 43, 85 in 100 |
| Independent places | 992 | 58, 83, 100 in 100 |
| Premium grocers within reach | 992 | 0, 0, 5.4. Half the areas have none |
| Mid-range grocers within reach | 992 | 0, 1.8, 16.4 |
| Value grocers within reach | 992 | 0, 0.4, 3.5 |
| Premium gyms within reach | 992 | 0, 0, 1.5. 958 areas have none |
| Mid-range gyms within reach | 992 | 0, 0, 3.9 |
| Value gyms within reach | 992 | 0, 0.1, 3.4 |
| Premium coffee within reach | 992 | 0, 0, 3.2. 788 areas have none |
| Mid-range coffee within reach | 992 | 0, 1.0, 40.4 |
| Value coffee within reach | 992 | 0, 0.2, 3.1 |

The nearest place of a tier has a figure where a place stands within 2,000 metres of half of an area's homes or more. By how many areas have one:

| | Premium | Mid-range | Value |
|---|---|---|---|
| Grocers | 735 | 1,002 | 933 |
| Gyms | 86 | 722 | 812 |
| Coffee | 322 | 995 | 886 |

The nearest place of a chain, by how many areas have a figure: Costa 989, Tesco 971, Sainsbury's 924, Greggs 886, Co-op 862, Iceland 701, Starbucks 682, Lidl 672, M&S 662, PureGym 650, The Gym Group 607, Pret 554, Anytime Fitness 539, Nero 535, Waitrose 442, Aldi 416, Asda 329, Gail's 322, Nuffield 281, Morrisons 177, David Lloyd 176, Virgin Active 160, Whole Foods 80, Blank Street 79, Barry's 78, Equinox 23, Ole & Steen 21, and none for Gymbox and Third Space. A measure with a figure for no area is left out of a release, and the release says so.

**Ten areas at the edge of London have no mix, no count and no share.** An output area is left out where homes outside London are within reach of it, as for cultural venues, and in those ten areas that leaves under half of the homes. A distance is held to no such rule: it is given where half of an area's homes or more have such a place within 2,000 metres, and is the middle distance of those homes.

## 5. The mix: what it follows, and whether a Londoner would know it

The mix is, of the places of a tier within 800 metres, the share that are premium, with a mid-range one counted as half. It was held against three other measures of the place, across the 990 areas that have one, as rank correlations:

| Against | Rank correlation |
|---|---|
| Homes per hectare | 0.04 |
| Distance from the middle of London | -0.21 |
| What homes sell for | 0.48 |
| Independent places | -0.15 |

| The fifth of areas with | Boroughs with most areas in it |
|---|---|
| The most premium mix | Westminster 18, Wandsworth 18, Kensington and Chelsea 17, Camden 16, Barnet 12, Richmond upon Thames 11, Bromley 10, Hounslow 9 |
| The least premium mix | Newham 19, Haringey 15, Hillingdon 14, Barking and Dagenham 13, Southwark 13, Enfield 11, Ealing 11, Redbridge 11 |

**Would a Londoner recognise it? Broadly, yes.** The boroughs at the premium end are the ones a person would name, and so are most at the other end. It is no map of the centre and no map of density, which is what most counts of venues turn out to be. It follows what homes sell for, as the founder meant it to, and not so closely that it says the same thing.

**Where it is weak.** The mix of an area rests on the places within reach of its homes, and in the outer boroughs those are few:

| Places of a tier within reach of a typical home | Areas |
|---|---|
| Fewer than 1 | 42 |
| Fewer than 2 | 173 |
| Fewer than 3 | 314 |
| Fewer than 5 | 553 |

Where few places stand behind it, one shop moves it a long way. Among areas with two or more, the mix follows what homes sell for at 0.53, with three or more at 0.58, and with five or more at 0.63. Nothing sets a least number of places yet: it is the founder's to decide ([0026](../../adr/0026-the-chains-in-a-place-are-measured-by-a-table-of-tiers.md)).

All three kinds are in one mix. Grocers and coffee are nearly all of it, because the file holds few gyms of any chain.

## 6. Independent places: what they follow, and whether a Londoner would know them

Independent places are, of the places to eat and drink within 800 metres, the share that the file gives no brand. Only places that a source that names chains gave are counted, on either side: 37,322 inside London, of which 29,831 belong to no chain, 80 in 100.

| Against | Rank correlation |
|---|---|
| Homes per hectare | 0.01 |
| Distance from the middle of London | -0.07 |
| What homes sell for | -0.10 |

| The fifth of areas with | Boroughs with most areas in it |
|---|---|
| The largest share of independent places | Hackney 21, Newham 15, Haringey 14, Lambeth 12, Lewisham 12, Ealing 10, Bromley 10, Greenwich 10 |
| The smallest share | Wandsworth 18, Westminster 14, Kensington and Chelsea 12, Croydon 11, Bromley 11, Harrow 10, Hounslow 9, Barnet 9 |

**Would a Londoner recognise it? No, not as the word is usually meant.** A person who asks for independent cafes is thinking of a certain kind of street. This figure is true to its name and says something else: where chains have not gone. That is some of the streets a person means, and it is also every parade of takeaways that no chain has taken a unit in. It is smallest in some of the smartest parts of London, where many places to eat are chains.

It is a share and not a count, so an area with four places to eat, none of a chain, stands at 100. It runs in a narrow band: three areas in four stand between 78 and 100.

**It is what two vibes were waiting for.** Food and drink holds it at 40 in 100 and Village feel at 25 in 100. Both can now be placed. Whether either should rest on it, as it is measured, is the founder's to decide.

## 7. What the first build with brands gave

London was built once with these measures, as a preview, from every list that holds a receipt. [The account of data builds](../../data-builds.md), section 25, has the command. The build is in a folder that git ignores.

| | |
|---|---|
| Measures carried | 76, of which 46 are of the brands, with independent places beside them |
| Measures of brands left out | Two: the nearest Third Space and the nearest Gymbox. Neither has a figure for any area |
| Ranked on | The mix, and the nearest place of each of 27 chains where a person asks for it by name. The 18 measures of the tiers are shown and never ranked on |
| Facts checked | 78,733, each with evidence behind it |

**Two vibes have a band that had none.**

| Vibe | It holds, in 100 | Areas with a band | The fifth of areas with most of it | The fifth with least |
|---|---|---|---|---|
| Food and drink | 80: places to eat and drink for each 1,000 homes, 40, and independent places, 40 | 992 | Hackney 20, Ealing 19, Southwark 19, Lambeth 16, Tower Hamlets 15, Newham 14, Islington 13, Haringey 12 | Croydon 19, Barnet 17, Bromley 12, Hounslow 11, Harrow 11, Merton 11, Hillingdon 10, Wandsworth 9 |
| Village feel | 60: independent places, 25, homes built before 1919, 20, and conservation cover, 15 | 969 | Hackney 22, Haringey 20, Lambeth 19, Lewisham 14, Newham 11, Ealing 11, Southwark 11, Islington 10 | Hillingdon 17, Harrow 16, Croydon 14, Barnet 13, Havering 12, Hounslow 10, Bromley 10, Redbridge 9 |

- **Food and drink reads broadly as a Londoner would expect**, with one surprise: the West End is not at the top, because so many of its places to eat are chains.
- **Village feel does not find villages.** Since this build was made, core places it only where the size or the shape of a town centre has a figure, so a build made now places no area on it ([the contract](../../design/contract.md), section 3.2). It holds 60 in 100 of its recipe, which is the least a band is given on, and none of that is the size or the shape of a town centre. What it finds is inner London's old streets where few places are chains. It follows homes built before 1919 at 0.73. It is served as soon as a release carries it, so whether it is served is the founder's to decide before one does.
- Everyday on foot still holds 45 in 100, and has no band.

**A firm budget of 400,000 pounds for a flat leaves out 397 of the 1,002 areas.** 530 areas have a flat at or under it. 75 have no price for a flat: each is kept, says that its cost is not known, and stands below every area that has one.

## 8. The row of the proxy audit

[Decision record 0006](../../adr/0006-rank-places-not-residents.md) asks for this row before a measure is served. It covers the mix of brands, the places and the nearest place of each tier, the nearest place of each chain, and independent places. It was written on 2026-09-24, before any release held one of them. Nobody has reviewed it.

| | |
|---|---|
| The aim it serves | To say which chains of grocers, gyms and coffee stand within reach of home, and how premium they are by the founder's table, so that a person who asks for a smart area, or a plain one, is offered a measure of the shops there. The founder's words are that brands give "an idea of 'quality' and socioeconomic factors" |
| Why it is in proportion | It counts shops, from a file of places, by the brand the publisher gives each. It holds nothing of who lives anywhere, who shops anywhere or what anyone earns. It is only ever offered: no word applies it, nothing weighs it by default, it stands in no vibe, and no likeness is counted on it. Every offer says that Burro measures places and not the people in them. A chain is weighed only where a person asks for it by name |
| What it was measured against | Other measures of the place, across London's areas, as rank correlations. The mix stands at 0.04 with homes per hectare, -0.21 with distance from the middle and 0.48 with what homes sell for. Independent places stand at 0.01, -0.07 and -0.10. Sections 5 and 6 hold the tables |
| What could not be measured | Whether the mix, or any of these, follows who lives in an area: the official measure of deprivation, income, or any count of residents by ethnic group, religion, country of birth, age or health |
| Why it could not | No file is registered for the audit alone, and no store holds one. No step that runs an audit is built. So no figure about residents was read, and no correlation with one is claimed |
| What is known all the same | The mix is wanted because it follows how well off a place is: that is the founder's aim, and it is why this row exists. It follows what homes sell for at 0.48, and what homes sell for follows what the people who buy them can pay. So the mix is a stand-in for the wealth of a place by design, and is likely to follow who lives there more closely than any measure Burro held before. How closely is not known |
| What triggers a review | A rank correlation of 0.5 or more, either way, between the mix and any figure of who lives in an area, across London's areas. It is the figure the row for recorded incidents set, and is the founder's to set |
| What can then be done | Show the mix on an area's page and rank on it no longer. Take it out of what is offered for a word for a smart area. Or leave it as it is served today: offered, never applied, and said to be of the place |

## 9. What is not done

| | Why |
|---|---|
| No second source of shops | The chains the file misses cannot be counted. A retailer's own list of its shops would need its own entry in the registry |
| No least number of places behind a mix | It is the founder's to set. Section 5 has what each choice would leave |
| No check of a sample of records by a person | Nobody has looked at whether a place the file calls a Waitrose is one |
| No audit against figures of residents | No file is registered for it. Section 8 |
| No way to drop the records of one source | Each place keeps the sources that gave it, so the records of one can be left out if a retailer objects. No switch does it yet |
