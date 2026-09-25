# High streets, and the second try at Village feel

Read and built on 2026-09-25. A dated snapshot, not a source of truth. Nothing here is legal advice. No lawyer has read it.

Every file was read through its receipt. Every count here was made by a program, and no person has checked one. No figure here is said of a named high street or of a named neighbourhood. A figure is said of London, or of a borough where it shows what a recipe finds. Whether a place is a village is a judgement. Section 5 says who made it: a program did, and no person has.

Greater London Authority - Contains public sector information licensed under the Open Government Licence v3.0. The Greater London Authority cannot warrant the quality or accuracy of the data. © Historic England 2026. Contains Ordnance Survey data © Crown copyright and database right 2026. The Historic England GIS Data contained in this material was obtained on 2026-09-24. The most publicly available up to date Historic England GIS Data can be obtained from HistoricEngland.org.uk. Source: Office for National Statistics licensed under the Open Government Licence v.3.0.

## 0. In short

| Question | Answer |
|---|---|
| Is Village feel mended | No. The founder's bar is that 30 of the 50 areas a recipe puts highest read as villages. The best recipe reached 24 |
| What the first try reached | 8 of 50 |
| What was read | The file of high street boundaries, for the first time, with the town centres and the conservation areas |
| What the file holds | 618 high streets, drawn as 640 rows. The file of town centres holds 234 centres |
| How many of London's homes have one within 800 metres | 90.4 in 100 have a high street, and 67.7 in 100 a town centre |
| What is built | One measure: how much of the nearest high street lies inside a conservation area. Core held no feature for it when this was written, so no release carried it. Since the decision of section 9 core names it, and a build carries it |
| How many areas have a figure | 925 of 1,002. The size and the shape of a town centre have a figure in 682 |
| What is served | Nothing new, when this was written: Village feel was held off, as it had been. Later on 2026-09-25 the founder chose to serve it as a rough guide: section 9 |
| What would mend it | Section 8 |

## 1. The file

| What | High street boundaries |
|---|---|
| Registry entry | `gla-high-street-boundaries`, approved for scoring alone |
| File | `GLA_High_Street_boundaries_2.gpkg` |
| Receipt | `f-5ce73f61b1c4` |
| Bytes | 4,427,776 |
| Edition | last changed 2025-06-19 |
| Period | As at 2025-06-19: the day the contents of the file were last changed. The file states no day its outlines are as at |
| Layers | One, `Table1`, on the National Grid |
| Rows | 640, each an outline in one piece |
| High streets | 618. A high street in several pieces is several rows under one id. 20 are, in 42 rows |
| Rows that enclose under a hundredth of a hectare | 17 |
| Columns | Seven: three numbers, the name, a size in hectares, the outline, and one the publisher's software keeps, which is empty in every row |
| A statement of rights | None. [The note of first ingest](../../../registry/evidence/gla-high-street-boundaries-2026-09-25.md) says what was looked for |

**The size the file gives is not read.** It is the same on every row of an id. Two pairs of high streets, each under ids of its own, are each given the size of the pair. So a size is what the outline encloses, as it is drawn.

| The ground a high street covers | Hectares |
|---|---|
| The least | 0.41 |
| The lower quarter | 6.52 |
| The middle | 9.56 |
| The upper quarter | 20.31 |
| The most | 222.35 |

**No name is read by a measure.** The name of a high street was read in a scratch folder, for a person to judge what a recipe finds, under the one use the registry gives the file. No name is in a tracked file, in a release or in a row of evidence.

## 2. How it stands to the town centres

| | |
|---|---|
| Town centres that share land with a high street | 207 of 234 |
| Town centres with half their outline or more inside a high street | 197 |
| High streets that share land with no town centre | 403 of 618 |
| Land inside a high street | 10,862 hectares |
| Land inside a town centre | 4,093 hectares, of which 2,906 lie inside a high street |
| Homes with a high street within 800 metres, in a straight line | 90.4 in 100 of London's |
| Homes with a town centre within 800 metres | 67.7 in 100 |
| Homes with either | 92.2 in 100 |
| Output areas nearer to homes beyond London than to any high street | 231 of 26,369. For the town centres it is 717 |

**The file of high streets holds most of the town centres, and two high streets in three that are no town centre.** So it is the file to ask about the centre a home has, and the file of town centres is the file to ask which centres are large.

**A high street is drawn wider than a town centre.** 195 town centres have half their outline or more inside one high street, and in the middle that high street is two and a half times the size of the town centre. So the line that called a town centre small, 10 hectares, means nothing of a high street, and was not carried over.

**It does not draw every village.** The founder named seven places as villages. The file draws a high street under the name of six. It draws none for the seventh: the homes there are given a high street of the next place.

## 3. The measure

`derive/highstreet_conserved.py` works it out, and its first lines say how. In short:

1. The conservation areas of London, each once, joined so that land inside two is counted once.
2. For each high street, the land of it that lies inside a conservation area, over the land of it in an authority that sent a conservation area. The tidal river is no land.
3. For each output area, the share of the nearest high street, where one is within 800 metres and no nearer one may stand beyond London.
4. For each area, the mean over its homes. Below half the homes with a share, no figure.

| | High streets | Town centres, asked the same |
|---|---|---|
| Outlines with a share | 617 of 618 | 234 of 234 |
| Nought | 257 | 72 |
| Half or more | 118 | 69 |
| 90 in 100 or more | 27 | 20 |
| All of it | 9 | 3 |
| The middle | 6.1 in 100 | 20.1 in 100 |

One high street has under half of its outline on land that is known, and has no share.

| The figure of an area | |
|---|---|
| Areas with a figure | 925 of 1,002 |
| Every home has a share | 670 |
| Some homes have none | 255 |
| Under half the homes have one, so no figure | 70 |
| No home has one | 7 |
| The lowest, the middle, the highest | 0.0, 12.7 and 100.0 |
| Areas that read nought | 162 |

**It follows the centre of London, as every part of the old recipe did.** Across the areas it stands in the order of conservation cover at 0.73, of distance from the City of London at -0.52, of homes per hectare at 0.44 and of what a home sold for at 0.37. Inner London is largely conservation area, so its high streets lie inside one. By itself the measure is no list of villages.

## 4. Three recipes

Each was worked out in a scratch folder, for all 1,002 areas, as core works a vibe out: where an area stands among London's areas on each part, weighted, and no band under 60 in 100 of the recipe.

| Recipe | Its parts, in 100 |
|---|---|
| The first try | Independent places 25, a small centre 20, a compact centre 20, homes built before 1919 20, conservation cover 15 |
| A | How small the nearest high street is 25, the high street in a conservation area 35, homes built before 1919 20, conservation cover 20 |
| B | As A, and the conservation area of a high street counts only where the high street is under 20 hectares |
| C | The high street in a conservation area 45, homes per hectare read from the low end 30, homes built before 1919 15, conservation cover 10 |

**Why C.** A and B put inner west London first. What tells a village from an old street of inner London is that its homes stand apart: the fifty areas A puts highest hold 61 homes to the hectare in the middle, and the areas round the seven places the founder named hold between 5 and 31. So C reads homes per hectare from its low end. It has no part for the size of a high street: a part for size let the small parades of inner London in, and took out the villages whose high street is drawn large. The high street is 45 in 100 of it, so no area is placed without one, and the two parts that rest on the conservation areas are 55, so they place no area alone.

| | A | B | C |
|---|---|---|---|
| Areas with a band | 926 | 926 | 925 |
| Rank correlation with homes per hectare | 0.43 | 0.27 | 0.08 |
| With distance from the City of London | -0.56 | -0.44 | -0.28 |
| With what a home sold for | 0.48 | 0.46 | 0.45 |
| With conservation cover | 0.81 | 0.68 | 0.74 |
| Boroughs among the fifty highest | 16 | 17 | 22 |
| Boroughs with no area in the highest band | 4 | 3 | 3 |

| Recipe | Boroughs with most areas among its fifty highest |
|---|---|
| A | Kensington and Chelsea 12, Westminster 6, Camden 5, Haringey 5, Richmond upon Thames 5, Islington 4, Lambeth 3 |
| B | Kensington and Chelsea 10, Camden 6, Westminster 6, Richmond upon Thames 5, Haringey 4, Lambeth 4, Islington 3 |
| C | Haringey 8, Richmond upon Thames 8, Barnet 4, Bromley 3, Greenwich 3, Hounslow 3, Redbridge 3 |

| Recipe | Boroughs with most areas in its highest band, which is a fifth of the areas |
|---|---|
| A | Kensington and Chelsea 19, Camden 17, Haringey 16, Hammersmith and Fulham 15, Westminster 14, Lambeth 13, Islington 12 |
| B | Kensington and Chelsea 17, Camden 15, Haringey 15, Lambeth 15, Lewisham 13, Westminster 13, Hammersmith and Fulham 11 |
| C | Kensington and Chelsea 18, Richmond upon Thames 16, Haringey 15, Hammersmith and Fulham 14, Westminster 12, Hounslow 10 |

## 5. How each fifty was read

Each of the fifty areas a recipe puts highest was read by the name of its nearest high street and its borough alone, as a village, as no village, or as cannot say. Three readings were made. One is the builder's, who made the recipes. Two are of readers who were told nothing of any recipe, and were handed every high street of every recipe in one list, in an order that says nothing. Each reading was made by a program, from what it holds of London, and by no person who knows the places. The founder may overrule any reading.

| Of the fifty highest | The first try | A | B | C |
|---|---|---|---|---|
| Read as a village, by the builder | 8 | 10 | 8 | 24 |
| By the second reader | | 11 | 9 | 24 |
| By the third reader | | 9 | 7 | 23 |
| Read as no village, by the three | 39 | 30, 33, 33 | 31, 34, 34 | 8, 14, 15 |
| Cannot say, by the three | 3 | 10, 6, 8 | 11, 7, 9 | 18, 12, 12 |

The three readings agree on 107 to 111 of the 119 high streets that were read. The reading of the first try is the one that was made of it at the time, by a reader of its own.

**C finds three times what the first try found, and does not clear the bar.** Its first fifty are in 22 boroughs, and 8 of them stand within 8 kilometres of the City of London.

**Where the seven fall.** The founder named seven places as villages. Each is taken to stand in the area most of whose homes are nearest to its own high street, and the one the file draws no high street for, in the area where Ordnance Survey puts its name. Under C those areas are placed between 3 and 37 of 925, and every one is in the highest band. Under A they are placed between 39 and 83, and under B between 33 and 218. Which high street is a village's own is the builder's reading.

**What C still gets wrong**, by kind and with no name:

| Kind | Of C's fifty | What it is |
|---|---|---|
| Read as a village by all three | 23 | |
| Read as a village by one of the three | 2 | |
| A trunk road or a busy high road inside a conservation area | 7 | The measure counts land inside a line. It cannot tell a village street from a main road through old streets |
| A large centre, or a centre beside a large park | 5 | Homes per hectare is counted over all the land of an area, so a park in it makes its homes read as standing apart. And no part of C says how large a centre is |
| A parade that stands near a village, and is not its centre | 6 | A home is given the high street nearest to it. The readers could not say, or said no |
| An old centre that the readers could not place, or took for no village | 7 | It may be a village. Of these and the parades, ten were read as cannot say by all three |

Which kind a high street is of is the builder's reading, made from its name, its size and the homes per hectare of the area.

## 6. Other recipes that were looked at

| What was changed in C | Read as villages, of fifty, by the three |
|---|---|
| Nothing | 24, 24, 23 |
| The weights 40, 30, 15 and 15 | 23, 23, 22 |
| A part for how small the high street is, at 10 | 22, 22, 21 |
| Flats, read low, in place of homes per hectare | 19, 19, 18 |
| Gardens in place of homes per hectare | 14, 14, 13 |
| The conservation area counted only where the high street is under 20 hectares | 25, 24, 24 |
| No part for homes built before 1919 | 26, 26, 25 |
| Two parts alone: the high street 55, homes per hectare 45 | 26, 26, 25 |

**A search was made of every simple recipe**, to see what the parts that are held could reach at the most: 65,000 recipes of three or four parts, of the high street in a conservation area with any of fifteen other figures. The most that any reached is 29 of 50 read as villages by two readers or more. Such a recipe is fitted to the readings, so none is put forward. Every one that reached it holds homes per hectare, read low, at 20 to 35 in 100, with homes away from main roads, or gardens, at 5 to 15.

## 7. Is C a vibe of villages, or of old and costly inner London

| The fifty highest | A | C | London's middle area |
|---|---|---|---|
| Kilometres from the City of London, the middle | 7.2 | 12.1 | 12.1 |
| Within 8 kilometres of it | 31 | 8 | |
| What a home sold for, the middle | 857,500 pounds | 763,750 pounds | 522,125 pounds |
| Among the dearest fifth of London's areas | 39 | 29 | |
| Homes per hectare, the middle | 61.4 | 17.0 | 32.2 |
| Homes built before 1919, the middle | 68.0 in 100 | 39.2 in 100 | 23.4 in 100 |

**At its top, C is no vibe of inner London.** Its fifty highest stand as far from the City as London's middle area does.

**It is a vibe of old and dear places all the same.** 29 of its fifty highest are among the dearest fifth of London's areas, and it follows what a home sold for at 0.45, as A does at 0.48. The places that are called villages in London are old and dear, so a recipe that finds them follows both. What a home sold for is no part of any recipe.

**Below its top it is still much of inner west London.** A vibe is said as a band, and the highest band is a fifth of the areas. Of the 185 areas in C's highest band, 62 stand within 8 kilometres of the City and 100 are among the dearest fifth. Kensington and Chelsea has 18 of its 21 areas in it.

## 8. What would mend it

| What | Why | Where it stands |
|---|---|---|
| A person who knows the places reads C's fifty | Ten of the fifty were read as cannot say by all three readers. The count of villages turns on them | The list is in a scratch folder, with the three readings beside each area |
| How much traffic runs along a high street | To tell a village street from a trunk road inside a conservation area. It is the largest kind of error that a figure could mend | Not looked for on this try. Since then the registry holds the Department for Transport's counts as approved, as `dft-road-traffic-counts`, and the list `m13-road-traffic` names the file |
| Homes per hectare of the land that is no park | So that a park does not make the homes beside it read as standing apart | It can be made from files that are held. Core holds no feature for it |
| An outline for a village centre the file does not draw | One of the seven places has no high street of its own in the file | Not known to be published. Ordnance Survey's retail areas are held in the registry as premium |
| A name for each area that a person knows | A reader judged an area by its nearest high street. An area of a village whose nearest parade is on a main road was read as no village | A build can give each area a drafted name. The readings were not made with one |

## 9. What was decided

Nothing changed in core. Village feel places an area only where the size or the shape of its town centre has a figure, and no build carries either, so no build places an area on it. A wish for it is turned away as it was. [Decision record 0013](../../adr/0013-vibes-are-the-centre.md) records the second try.

The measure is worked out by its module, and is on no list of a build. If the founder decides to serve a recipe that holds it, core gains a feature under the id `highstreet_conserved`, and a test of the measure then fails until it joins the list.

**Later on 2026-09-25 the founder decided to serve it.** They were shown that no try had reached the bar, and chose to serve Village feel as a rough guide, on recipe C with no share changed. Core names the measure `highstreet_conserved`, a build carries it, and Village feel says wherever it is shown that it is a rough guide, and why. It is never taken without a press of its own. [Decision record 0013](../../adr/0013-vibes-are-the-centre.md), as amended, has the decision and what each try counted. What section 8 lists would still mend it, and the bar is what would make it as sure as the other vibes.
