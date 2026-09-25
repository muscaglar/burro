# 0031. The traffic near homes is a measure, and an area with no figure is never taken to have little

Status: accepted, 2026-09-25. The founder asked how Burro gets traffic information, and asked that the work be finished the same day. What is chosen here is a first choice, made so that there was something to look at. The last section says which choices are the founder's to overturn, and the section before it how each is reversed.

## Context

A person who asks for a quiet place means, more than anything, little traffic. Burro held no figure of traffic. Quiet streets was made of three parts: the share of homes within 100 metres of a main road, which is the class of a road and says nothing of how busy it is; the share of homes near a cluster of pubs and bars; and the share of residents exposed to transport noise, which is modelled for main roads, railways and airports. A build of London shows main roads and ranks no area on them alone, so "away from main roads" was answered "not in this data".

The Department for Transport publishes, once a year, its estimate of the motor vehicles that pass each of its count points on an average day: the annual average daily flow. The file is of Great Britain and is published under the Open Government Licence. The registry held its entry, for want of a measure that needed it. A measure of the traffic through the nearest high street had been built from it, for a third try at Village feel, on a branch that was never joined.

Missing data is never filled in (rule 7), and the file is full of what is missing: the publisher counts every link of a main road, and only a sample of the minor roads. A street nobody counted has no figure. That is not a figure of nought.

## Decision

**The traffic near where homes stand is a measure, `road_traffic_nearby`. A person may rank on it, and it is a part of Quiet streets. An area with no figure is never placed or ranked as though it had no traffic.**

| | |
|---|---|
| What is measured | The motor vehicles that pass, on an average day of a year, the busiest count point within 500 metres of home, in a straight line. A motor vehicle is every vehicle but a pedal cycle |
| From what | The Department for Transport's file of the flow at each count point, `dft-road-traffic-counts`, which the registry holds as approved since 2026-09-25. One file, of Great Britain |
| Which year | Each count point is read at the latest year it has a figure for. The measure says the years its figures are of, and how many were counted and how many estimated |
| Where a home stands | At the point the statistics office gives as the centre of population of its output area, as every measure of nearness takes it |
| The figure of an area | The mean over its homes, to the whole vehicle. Where under half the homes have a figure, the area has none |
| Two count points near one home | The home is given the busiest. The flows of two count points are never added together: two points on one road count the same vehicles |
| No count point near a home | No figure. Never nought, never the flow of a road further off, and never a figure for a class of road |
| What kind of measure | A nuisance, as main roads and noise are: less of it is the wish itself, and nobody can ask for more. It is `modelled`, because the publisher gives an estimate and no reading. No likeness between areas counts it |
| In Quiet streets | 20 in 100. It took its share from main roads, which were 40 and are 20. Clusters of pubs and bars and transport noise are 30 each, as they were |
| In any other vibe | None. Gritty holds main roads and transport noise, and is as it was decided on 2026-09-24. Village feel is as the founder chose to serve it |
| An area with no figure, in the vibe | The part is left out and the rest is weighed again, by the rule of every recipe. Its band rests on 80 in 100, and its fact says on how many parts |
| An area with no figure, where traffic is asked for by itself | It stands below every area that has one, and says what it lacks ([0024](0024-an-area-with-no-figure-for-what-was-asked-stands-below.md)). Where nothing else was asked for that is known of it, it is not ranked, and says why |
| The words | "No traffic", "less traffic", "low traffic", "no busy roads". A main road is asked of as the homes beside one and as the traffic near home, so "away from main roads" is answered with traffic where main roads alone are not ranked on. A quiet road is a quiet street, which is the vibe. "Not on a busy road" is offered for one press and never applied: "on" is no word the rules place |
| What is said with the figure | The publisher's credit, and the note it asks for: that its estimates for a road link are less robust than its figures for a region or for the country. The registry holds both, and a release carries them to every fact |
| The measure of the high street | Left out. One measure that is used is better than two, and the first try at it was for a vibe whose recipe is not to change |

The catalogue is at version 15 and the engine at 1.15.0. The contract stays at version 2: one id was added to a list of codes, and no record changed its shape.

## Why 500 metres, and why the busiest

The distance is one line, `TRAFFIC_WITHIN_M` in core's catalogue, and stands in the label of the measure. It was chosen on the file, held against London's homes, and a test holds each figure below to the files.

| Within | Areas of London's 1,002 with a figure | Of the homes that stand within 100 m of a main road, those with a count point of a major road within reach |
|---|---|---|
| 300 m | 578 | 62 in 100 |
| 500 m | 943 | 84 in 100 |
| 800 m | 1,000 | 96 in 100 |

The middle link of a major road near London's homes is 0.8 km long, with one count point on it. At 300 metres four areas in ten have no figure, and a home on a main road often has none of its own road. At 800 metres nearly every area has a figure, and nearly every home is given the same few arterial roads, so the figure says little. 500 metres is between.

The nearest count point would give a home beside a main road the flow of the side street behind it. The sum would count one road twice. The busiest is what a home lives with.

## What was found on London

Worked out by a program on 2026-09-25, from the file as it was retrieved that day. No person has checked a figure, and none is given here of a named place.

| | |
|---|---|
| The file | 600,551 rows, of 46,754 count points, of the years 2000 to 2025 |
| Homes with a count point within 500 metres | 87 in 100 |
| Areas with a figure | 943 of 1,002. 59 have none |
| The count points behind the figures | 2,555. 1,414 were counted in the year they are of and 1,141 were estimated by the publisher. 1,466 are of 2025 |
| How traffic follows the other parts of Quiet streets | A rank correlation of 0.42 with main roads, 0.45 with transport noise and 0.19 with clusters of pubs and bars. It says something the others do not |
| Quiet streets, against the build before | 271 of the 1,002 areas stand in another band: 136 in a quieter one and 135 in a busier one, all but three by one band. 35 of the first fifty were among the first fifty before. The order of the areas before and after has a rank correlation of 0.96 |
| The 59 areas with no figure | Each is placed on Quiet streets, on the other 80 in 100 of the recipe. 43 of them stand in the two quietest bands: they have half as many homes beside a main road as the rest. Had no figure been read as no traffic, they would stand a middle of 74 places higher, and 13 of them would be among the first fifty, where 5 are |
| A search for little traffic and nothing else | Ranks the 943 areas that have a figure. The 59 are not ranked, and the answer says of each that it has no figure of traffic |
| The three searches that are held against every build | The two that ask for Quiet streets kept 9 and 8 of their first ten. The third asks for no quiet, and kept its ten in their order |
| What else moved | Nothing. No figure of any other measure, no band of any other vibe, no cost, no area and no other file |

## Consequences

- **A person can ask for little traffic and be answered**, in a build that ranks no area on main roads alone.
- **Quiet streets knows how busy the roads are, and not only what class they are.** On London 271 areas changed band, and the first of the list are still outer streets with no main road, no cluster of pubs and little noise.
- **Six areas in a hundred have no figure, and they are the quieter ones.** A quiet street is less likely to have a count point than a busy one. So the areas with no figure are never the first of a search for little traffic, though some of them may deserve to be. What the measure cannot see says so on the page of methods.
- **A main road a few streets away reads as the traffic of a quiet street.** The measure takes the busiest count point within 500 metres of the centre of a small census area, and knows nothing of what stands between.
- **A figure may be years old.** A minor road that left the publisher's sample keeps the figure of the last year it was counted. The measure says the span of years of what it read.
- **The made-up city has made-up traffic**, which follows its made-up main roads area for area. So no band of the made-up city moved, and what traffic adds is seen on real data alone.
- **A second city has the measure on day one.** The file is of Great Britain, and no word of the step names a city.
- **One more file is fetched at a refresh, once a year.**

## What reverses it

| To | Do this | What follows |
|---|---|---|
| Change the share of traffic in Quiet streets | At the panel, on the screen of the vibe: each share may be set from 1 to 59 in 100. It is written to the file of changes ([0029](0029-a-change-reaches-a-release-through-a-file-of-changes.md)) and reaches the next build | Every band of Quiet streets may move. The panel shows how many before the change is kept |
| Take traffic out of Quiet streets | In core: the recipe in `catalogue.py`, put back to main roads at 40, with the version of the catalogue raised | The same. `moved` says how many |
| Change the distance | `TRAFFIC_WITHIN_M`, one line. The label follows it. The id of the derivation in the module names the distance, and changes with it | The figures the test on the real files holds are worked out again, and the catalogue's version is raised |
| Show it and rank on it no longer | `RANKABLE = False` in `derive/road_traffic_nearby.py`, as main roads are carried | It stays a part of Quiet streets and is shown on an area's page. "No traffic" is then answered "not in this data" |
| Leave the measure out of a build | Build without the list `m13-road-traffic` | The build says by which rule it left the measure out. Quiet streets rests on 80 in 100 in every area, and places them all |
| Withdraw the source | Set the registry entry back to `held`, and say why | The gate refuses the file, and every build leaves the measure out |
| Bring in the measure of the high street | It is on the branch that was never joined, as one commit. It needs a name of core's and a recipe that wants it | |

An id is never renamed and never used again for another thing, so `road_traffic_nearby` stays in core whatever is reversed.

## What is not settled

| Matter | Whose | What stands today |
|---|---|---|
| The distance | The founder's | 500 metres |
| The shares of Quiet streets | The founder's, at the panel | 20 main roads, 20 traffic, 30 clusters of pubs and bars, 30 transport noise |
| Whether Gritty should hold traffic | The founder's | It does not. Its recipe holds main roads at 15 and transport noise at 10, and traffic follows both |
| Whether a quiet road is the vibe, or traffic alone | The founder's | The vibe, as a quiet street is |
| Whether "away from main roads" should weigh traffic | The founder's | It weighs both, and a build of London applies traffic alone |
| Whether a figure of many years ago should count | The founder's | Every count point is read at its latest year, however old. Reading the last five years alone would leave more areas with no figure |
| Whether the areas with no figure should say so on a card | The founder's | An area's page says it has no figure. A card says it only where traffic was asked for |
| The credit | A person's, by opening the publisher's page | The wording of the licence. `attribution_verified` stays false until a person has read it |
