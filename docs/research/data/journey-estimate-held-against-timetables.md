# The journey estimate, held against the timetables

Status: measured on 2026-09-25. It holds the estimate of [decision record 0027](../../adr/0027-a-journey-is-estimated-from-distance-until-a-timetable-is-held.md) against journeys timed from Transport for London's timetables, as they were fetched on 2026-09-24. It is a dated snapshot. **It changes no number that is served.** The numbers of the estimate are the founder's, and the last section recommends. **The founder decided one of them later the same day**: recommendation 2 of section 7 was taken, and `WITHIN_BY` is 10. Every count on this page is of the estimate as it was, with `WITHIN_BY` at 5, but where a table says otherwise.

No figure here is said of a named area or of a named station, and none is named. A line is given by the code in the name of its file, as the list of files gives it. The figures on this page are counts over London. Every other figure is in a scratch folder that is in no repository.

No page of any publisher was read for this work, because nothing was fetched. Where a source is named for a number, it is named from what is known of it, and the number is to be checked in a browser before anything rests on it.

## 0. In short

| Question | Answer |
|---|---|
| Is the estimate good enough to leave areas out on | Yes, where it could be checked. Of the 775 journeys that a firm limit of 40 minutes leaves out, none is timed within 40. Nor is any at 30 or at 45. At 60 it is 1 of 193 |
| What is its fault | It is short, and so it keeps too much. The timed journey is 6 minutes longer in the middle. Half of the journeys that a firm limit of 40 keeps are timed beyond 40, and so is 1 in 5 of those it calls likely within |
| How sure is that | The 6 minutes rest on three numbers that are this measure's own: how much further a walk is than a straight line, the way between a street and a platform, and a change. With all three taken short it is 2 minutes, and with all three taken long 11. In all three no journey is left out at 40 that is timed within it |
| Where could it be checked | 384 of 1,002 areas, which hold 38.5 in 100 of London's homes: the areas whose homes are nearest a station of the Underground or the DLR. And for journeys by those two alone |
| What cannot be checked | 588 areas, which hold 58.6 in 100 of the homes, are nearest a railway station. No file that is held has its trains. In the founder's own search, 333 of the 422 areas left out were not timed, and 305 of them are nearest a railway station |
| Is one number for all of London the fault | No. A number for each line fits no better on the areas it was not fitted on. The fixed part is the fault: 12 minutes, where the timed journeys ask for about 18 to 22 |
| What is recommended | Leave out as now. Promise less: `WITHIN_BY` from 5 to 10. Give no number by line. Put the timed journey in the place of the estimate when a build holds one. Section 7 |

## 1. What the file holds

The file is `tfl-journey-planner-timetables`, edition 21092026, as [the list of files](../../../packages/pipeline/src/burro_pipeline/fetch/lists/m5-journeys.toml) and its receipt describe it. It was read through the pipeline's `Inputs`, for the use `routing`, under the lock of the build.

| Asked | Answer |
|---|---|
| Its form | A zip of six zips. They hold 826 files of XML in TransXChange, each one service of one line |
| What was read | The 40 files of the Underground and the DLR, which are in the fifth zip: 35 of the mode `underground` and 5 of the DLR, by the names of the files |
| What was not read | 732 timetables of buses, 46 of buses that run in place of a train, 4 of the river, 3 of trams and 1 of the cable car |
| What it lacks | The London Overground, the Elizabeth line and National Rail. No file is named for any of them |
| The day that was timed | Wednesday 23 September 2026. It is in the middle of a week, is no bank holiday, and is within the dates of a file of every line |
| How many files run on that day | 12 of the 40: one for each of the 11 lines of the Underground, and one for the DLR. The other 28 are of other days |
| How many journeys | 10,416 on the day, which make 218,127 hops from one call to the next, at 723 platforms |
| How many in the morning | 1,932 journeys make a call that leaves between 07:00 and 09:29 |

**Why the day matters.** A line may have two files that hold one day: a timetable for the season, and one for a few days of works. On Wednesday 30 September 2026 three lines have two each. A reader that took every file would count the trains of those lines twice. `on_the_day` refuses such a day, and the day that was timed has none. The Tuesday and the Thursday of the same week hold the same 10,416 journeys. Wednesday 14 October 2026 holds 10,394.

**How a run time is read.** No call has a time of its own. A journey states when it first leaves, and names a pattern. The pattern is a chain of links, each with the stop at either end, a `RunTime`, and a `WaitTime` where a train stands. The time of a call is the time the journey first leaves, and every run and every wait before the call. On the day that was timed every run from one call to the next is a whole number of minutes, and the middle one is 2. A train stands at 4,623 of its 228,543 calls, and all but 3 of those are on the DLR.

**How the time between two trains is read.** It is stated nowhere: no journey is given as "every so many minutes". It is the time between the calls that two journeys make at one platform, one after the other.

| Code of the line | Journeys on the day | With a call that leaves from 07:00 to 09:29 | Minutes between trains at a platform, in the middle |
|---|---|---|---|
| BAK | 617 | 106 | 3 |
| CEN | 1,046 | 197 | 4 |
| CIR | 257 | 44 | 10 |
| DIS | 1,017 | 197 | 4 |
| HAM | 233 | 40 | 10 |
| JUB | 872 | 174 | 2 |
| MET | 756 | 148 | 5 |
| NTN | 1,573 | 295 | 3 |
| PIC | 831 | 170 | 3 |
| VIC | 1,099 | 208 | 2 |
| WAC | 531 | 92 | 3 |
| DLR | 1,584 | 261 | 5 |

The minutes between trains are of each platform's own trains, from 07:00 to 09:29, and the figure is the middle over the platforms of a line. Two lines that share a platform are counted apart here, and together where a journey is timed.

## 2. How a journey is timed

`travel/transxchange.py` reads the file, and `travel/timed.py` times a journey. Each is tested on a made-up town, where every journey is worked out by hand beside its test.

**The question.** A person must be at a place by a time. When is the last moment they can leave home? The journey is what lies between. It is asked for every minute from 08:00 to 09:30, which is 91 times, and the journey of an area is the one that half of those minutes do at least as well as.

A journey is the walk from home to a platform, the wait, the time on each train, each change, and the walk from the last platform to the place. **It is made on the Underground and the DLR alone.** Where walking all the way is quicker, the journey is the walk.

Every number below was written down before any journey was timed.

| What is assumed | Number | Where it is from |
|---|---|---|
| How fast a person walks | 4.8 km an hour | The travel design's own setting. It is also what Transport for London's measure of access to public transport walks at, 80 metres a minute |
| How much further a walk is than a straight line | 1.3 times | This measure's own. No network of streets is built, so no walk can be measured. Studies of walking put the figure between about 1.2 and 1.4 |
| How long the wait is | Nothing is assumed | A person leaves so as to meet a train, and is early by what the timetable makes them. Over the 91 minutes that comes to half the time between trains where they are even, which is what Transport for London's measure takes for a wait |
| The way between a street and a platform | 2 minutes, at each end | This measure's own. No file that is held gives the way through a station |
| A change between two platforms | 4 minutes, and the walk between the two where they stand apart | This measure's own, for the same reason |
| A change at one platform | 1 minute | The travel design's own slack before boarding |
| The longest walk to a platform or from one | 2,400 metres in a straight line | The travel design's own first guess |
| The longest walk between two platforms | 800 metres in a straight line | The travel design's own first guess |
| The longest journey | 120 minutes | The travel design's cutoff |
| Where a home is | The centre of population of its output area | As every measure of the release takes it |
| The journey of an area | The lower median over its output areas, by homes | The travel design's own roll-up |

Three numbers are this measure's own, and how short the estimate is found to be leans on them. So every count was made twice more:

| Set | A walk | Between a street and a platform | A change |
|---|---|---|---|
| Short | 1.2 times the straight line | 1 minute | 2 minutes |
| As assumed | 1.3 | 2 | 4 |
| Long | 1.4 | 3 | 6 |

**Three checks that the timing is sound.** The distances to the nearest station of the Underground or the DLR were worked out again with the release's own code, and are the release's own figure for all 1,002 areas. The platform the file places stands 8 metres further from a home than the way in the release measures to, in the middle. And from a platform to a place with no change, which is 771 journeys, the timed journey is 3 minutes longer in the middle than the way in, the quickest ride of the morning and the way out: that is the wait. Eight in ten are between 1 and 7 minutes longer.

**What it cannot see.** A delay, a closure, a full train, which door of a station is open, and a bus to the station. A home more than 2,400 metres from any platform has no journey. And a train that is not held: section 6.

## 3. What was timed

| Thing | Count |
|---|---|
| Places to reach | 7 stations of the release, as they were asked for. One is the station of the founder's own search |
| Areas whose homes are nearest a station of the Underground or the DLR | 385 of 1,002 |
| Of those, timed | 384. The homes of one stand too far from any platform to walk |
| Journeys timed | 2,688: 384 areas to 7 places |
| Homes of the areas timed | 1,318,440 of 3,423,767, which is 38.5 in 100 |
| Boroughs with an area timed | 28 of 33 |
| Areas timed that the estimate takes to be near the Underground | 311 of the 384. The other 73 are further than 800 metres from it |

An area is nearest the Underground or the DLR where the release's own distance to one is no greater than its distance to a railway station and to a tram stop. Each distance is the median over the area's homes, as every measure of the release is.

## 4. The estimate against the timed journey

The estimate is core's own, worked out by `estimated_minutes` and `band_against` on the release. Every count here is of the 2,688 journeys, with the numbers as assumed.

### 4.1 The bands

| Limit | Called likely within: timed within | timed beyond | Called borderline: timed within | timed beyond | Called likely beyond: timed within | timed beyond |
|---|---|---|---|---|---|---|
| 30 | 346 | 133 | 53 | 860 | 0 | 1,296 |
| 40 | 897 | 206 | 62 | 748 | 0 | 775 |
| 45 | 1,163 | 229 | 82 | 644 | 0 | 570 |
| 60 | 1,996 | 122 | 79 | 298 | 1 | 192 |

**What is called borderline is beyond, nine times in ten.** At 40 minutes 748 of the 810 journeys called borderline are timed beyond it.

### 4.2 The two kinds of wrong

They cost a person differently. An area that is left out and should not be is never seen. An area that is kept and should not be is seen, and is found out when the journey is looked up.

| Limit | Left out | Of those, timed within | Kept | Of those, timed beyond | Called likely within | Of those, timed beyond |
|---|---|---|---|---|---|---|
| 30 | 1,296 | 0 | 1,392 | 993, which is 71 in 100 | 479 | 133, which is 28 in 100 |
| 40 | 775 | 0 | 1,913 | 954, which is 50 in 100 | 1,103 | 206, which is 19 in 100 |
| 45 | 570 | 0 | 2,118 | 873, which is 41 in 100 | 1,392 | 229, which is 16 in 100 |
| 60 | 193 | 1 | 2,495 | 420, which is 17 in 100 | 2,118 | 122, which is 6 in 100 |

By homes the shares are within 2 in 100 of these. At 40 minutes, of the 775 left out, the journey nearest the limit is timed at 43 minutes. Of the 954 kept and timed beyond, the middle one is 9 minutes over, and 382 are more than 10 over. Of the 206 called likely within and timed beyond, the middle one is 4 minutes over, and 20 are more than 10 over.

### 4.3 The same, with the numbers taken short and long

| At 40 minutes | Short | As assumed | Long |
|---|---|---|---|
| Left out, and timed within | 0 of 775 | 0 of 775 | 0 of 775 |
| The left-out journey nearest the limit | 41 minutes | 43 | 46 |
| Kept, and timed beyond | 704 of 1,913 | 954 | 1,201 |
| Called likely within, and timed beyond | 75 of 1,103 | 206 | 410 |
| Called borderline, and timed beyond | 629 of 810 | 748 | 791 |
| The estimate less the timed journey, in the middle | 2 minutes short | 6 short | 11 short |

At 60 minutes the short set times 12 of the 193 left out within the limit, and the long set none.

### 4.4 How far the estimate stands from the timed journey

The estimate less the timed journey, in minutes. Below nought the estimate is short.

| Journeys | How many | The middle | Half lie between | Eight in ten lie between |
|---|---|---|---|---|
| All | 2,688 | -6.3 | -10.2 and -2.5 | -14.0 and 1.5 |
| Under 5 km | 462 | -5.8 | -9.4 and -2.5 | -12.5 and -0.2 |
| 5 to 10 km | 796 | -8.1 | -11.7 and -4.9 | -15.0 and -2.2 |
| 10 to 15 km | 718 | -6.8 | -10.5 and -3.4 | -14.8 and -0.4 |
| 15 to 20 km | 435 | -5.7 | -9.6 and -1.4 | -13.4 and 2.5 |
| 20 km and over | 277 | 1.9 | -3.7 and 6.8 | -8.3 and 11.7 |
| On foot all the way | 28 | -1.0 | -3.9 and 1.5 | -9.4 and 3.8 |
| One train, no change | 1,051 | -3.9 | -7.5 and -0.3 | -11.0 and 3.3 |
| Two trains, one change | 1,583 | -7.9 | -11.4 and -4.5 | -15.3 and -0.8 |
| Three trains, two changes | 26 | -10.6 | -15.1 and -3.0 | -19.2 and 4.0 |
| Near the Underground, at 2.5 a kilometre | 2,177 | -6.2 | -9.7 and -2.5 | -13.2 and 1.0 |
| Not near, at 3.0 a kilometre | 511 | -7.8 | -12.2 and -2.6 | -16.5 and 4.9 |

The estimate is within 5 minutes of the timed journey for 36 in 100 of the journeys, and within 10 for 73 in 100. The furthest it stands is 28 minutes, each way. From place to place the middle runs from 4.7 minutes short to 8.4 short.

**It is the changes, more than the distance.** The estimate is about as short at 3 km as at 18. It is 4 minutes short where no change is made, and 8 where one is. Three journeys in five make a change.

### 4.5 The founder's own search

A firm 40 minutes to one station, which leaves out 422 of the 1,002 areas.

| Of the 422 left out | Count |
|---|---|
| Nearest a railway station, and not timed | 305 |
| Nearest a tram stop, and not timed | 27 |
| Nearest the Underground or the DLR | 90 |
| Of those, timed | 89 |
| Of those, timed within 40 minutes | 0 |
| Of those, timed within 45 | 0 |
| The nearest to the limit | 50 minutes. With the numbers taken short it is 46, and long 53 |

| Of the 580 kept | Count |
|---|---|
| Timed | 295 |
| Of those, timed beyond 40 minutes | 160: 43 of them called likely within, and 117 borderline |
| Of those, timed beyond 50 | 76 |
| The same with the numbers taken short, and long | 117 beyond 40, and 207 |

## 5. Numbers that would fit better

None is applied. Each was fitted on half of the areas and counted on both halves. The halves are of areas and not of journeys, so that no area is counted on that a number was fitted on. Which half an area is in is decided by a hash of its id, and by nothing about the area: 191 areas and 1,337 journeys were fitted on, and 193 areas and 1,351 journeys were not.

### 5.1 The fixed part and the rate

| Numbers | Fixed minutes | Minutes a kilometre |
|---|---|---|
| As they are | 12 | 3.0, and 2.5 near the Underground |
| One fixed part and one rate | 20.7 | 2.41 |
| One fixed part and two rates | 21.9 | 2.80, and 2.16 near the Underground |
| The rates as they are, and the fixed part alone moved | 18.5 | 3.0, and 2.5 |
| With the walk the release holds | 15.7 | 2.06, and 15.0 for each kilometre to the nearest station |

With the numbers taken short the fixed part of the second row is 17.1, and long 24.2. The rate moves by less than 0.1.

| Numbers, with the bands as they are | Fitted on: off by, in the middle | nine in ten within | Not fitted on: off by, in the middle | nine in ten within |
|---|---|---|---|---|
| As they are | 6.9 | 14.1 | 6.8 | 14.1 |
| One fixed part and one rate | 4.3 | 11.5 | 4.2 | 11.0 |
| One fixed part and two rates | 3.8 | 10.0 | 3.8 | 9.5 |
| The fixed part alone moved | 3.9 | 10.9 | 3.9 | 10.3 |
| With the walk the release holds | 3.4 | 8.9 | 3.1 | 8.4 |

| At 40 minutes, with the bands as they are | Fitted on: left out | timed within | called likely within | timed beyond | Not fitted on: left out | timed within | called likely within | timed beyond |
|---|---|---|---|---|---|---|---|---|
| As they are | 360 | 0 | 566 | 106 | 415 | 0 | 537 | 100 |
| One fixed part and one rate | 513 | 4 | 302 | 8 | 581 | 1 | 300 | 11 |
| One fixed part and two rates | 506 | 2 | 318 | 6 | 562 | 0 | 293 | 3 |
| The fixed part alone moved | 513 | 2 | 351 | 11 | 583 | 1 | 338 | 12 |
| With the walk the release holds | 525 | 0 | 318 | 4 | 579 | 0 | 294 | 4 |

**The fit is not flattered.** Each set of numbers does as well on the areas it was not fitted on as on those it was.

**Two things the fits say of the shape of the estimate.**

1. **The fixed part is short, and the rate is a little high.** That is why the estimate is short at every distance under 20 km and a little long beyond it.
2. **Being far from a station costs a walk, and not a slower train.** The estimate gives an area that is not near the Underground a higher rate. Fitted apart, the two kinds of area have the same rate, 2.2 and 2.3 a kilometre, and fixed parts 9 minutes apart. The walk that the release already holds does more than the second rate does.

### 5.2 A number by the line a home is nearest

An area was given the line of the platform nearest its homes. A fixed part and a rate were fitted for each of the 9 lines that 5 areas or more of the fitted half are nearest, and the numbers for all were kept for the other 2 lines.

| On the areas not fitted on | Off by, in the middle | Nine in ten within |
|---|---|---|
| One fixed part and one rate for all | 4.2 | 11.0 |
| A fixed part and a rate for each line | 4.3 | 10.4 |
| One rate for all, and a fixed part for each line | 4.3 | 10.5 |

**It fits no better.** One line stands out, MET, whose trains make the longest runs between calls: one rate for all is 6 minutes long for it in the middle. For every other line that 5 areas or more are nearest, the middle is within 3 minutes of nought. What a number by line cannot hold is where the place is: whether the line a home is on runs to it, or a change is made.

### 5.3 The width of the borderline band

The band is 15 minutes wide: from 5 under the limit to 10 over it. Once the fixed part is fitted, nine in ten timed journeys are no more than 9.3 minutes over what is fitted, and nineteen in twenty no more than 10.4 under. So a band that is right nine times in ten where it says likely within, and nineteen in twenty where it leaves out, is about 20 minutes wide. No number makes it narrower: the spread is what distance alone cannot see.

The numbers as they are, and the bands alone moved, on the areas that nothing was fitted on:

| `WITHIN_BY` and `BEYOND_BY` | Left out at 40 | timed within | Called likely within | timed beyond | Called borderline | timed within |
|---|---|---|---|---|---|---|
| 5 and 10, as they are | 415 | 0 | 537 | 100, which is 19 in 100 | 399 | 31 |
| 8 and 10 | 415 | 0 | 442 | 44, which is 10 in 100 | 494 | 70 |
| 10 and 10 | 415 | 0 | 385 | 25, which is 6 in 100 | 551 | 108 |
| 12 and 10 | 415 | 0 | 321 | 11, which is 3 in 100 | 615 | 158 |

**Moving `WITHIN_BY` does what moving the fixed part does to what is promised, and leaves out nothing more.** With the fixed part at 18 and the bands as they are, the founder's own search would leave out 537 areas where it leaves out 422. Of the 115 more, 71 are areas that were not timed.

## 6. What cannot be checked

| Areas | How many | Homes | In 100 of London's homes |
|---|---|---|---|
| Nearest the Underground or the DLR, and timed | 384 | 1,318,440 | 38.5 |
| Nearest the Underground or the DLR, and too far to walk | 1 | 3,101 | 0.1 |
| Nearest a tram stop. Its trams are held, and were not timed | 29 | 95,286 | 2.8 |
| **Nearest a railway station, whose trains no file holds** | **588** | **2,006,940** | **58.6** |

Counted home by home, and not area by area, 2,096,750 homes are nearest a railway station: 61.2 in 100.

Four things follow.

1. **Nothing is known of three areas in five.** Where a train runs fast to a terminus, a journey may be shorter than its distance says. If the estimate leaves out an area that it should not, that is where it would be.
2. **The call is close for 59 areas.** They are counted as nearest a railway station, and the Underground or the DLR is no more than 100 metres further. A station that the two share is such a place.
3. **A timed journey is no shorter than the real one.** 158 of the 384 areas timed have a railway station within 960 metres of their homes. Where a train that is not held is quicker, a person takes it, and the real journey is shorter than the one timed. So the count of journeys kept and timed beyond is the most it can be. And an area that is left out and timed beyond may yet be within the limit by such a train: the timetables that are held cannot say.
4. **A journey was never timed by bus and called the journey.** The file holds the buses. A bus to a station, or in the place of a train that is not held, would be a journey of another kind than the one a person makes, and would say nothing of the estimate.

## 7. What is recommended

The numbers are the founder's to change. Nothing here was applied when it was written. **Recommendation 2 was decided by the founder on 2026-09-25**, and is in core since: [the decision record](../../adr/0027-a-journey-is-estimated-from-distance-until-a-timetable-is-held.md) has their words. No other row was decided.

| | Recommended | Why |
|---|---|---|
| 1 | **Leave areas out as now.** `BEYOND_BY` stays 10, over the estimate as it is | Nothing that is timed within 30, 40 or 45 minutes is left out, with the numbers taken short, as assumed or long |
| 2 | **Promise less.** `WITHIN_BY` from 5 to 10 | One number. At 40 minutes what is called likely within is then timed beyond 6 times in 100, where it is 19. Nothing more is left out. It is safe for the areas that cannot be checked: it only says less of them |
| 3 | **Do not move the fixed part alone** | It would leave out a quarter more areas in the founder's own search, most of them areas that were not timed. If the founder would have the minutes true to the clock, a fixed part of 18 with `WITHIN_BY` at 4 and `BEYOND_BY` at 16 says of every area what recommendation 2 says: each band is where it was, 6 minutes on |
| 4 | **Give no number by line** | It fits no better on the areas it was not fitted on |
| 5 | **Know what borderline holds.** Nine in ten of the journeys called borderline are timed beyond the limit | A person may read the word as an even chance. With `WITHIN_BY` at 10 it is 8 in 10 |
| 6 | **Put the timed journey in the place of the estimate, when a build holds one** | It is the one thing that takes the spread away: a change, and whether a line runs to the place. The record already says a time that is held takes the place of the estimate |
| 7 | **Time the rest when the rail schedule is held** | 588 areas wait on it. Until then nothing can be said of them, and this page says so |

## 8. How to do it again

| Step | With what |
|---|---|
| Read the timetables of a day | `timetables_in` and `on_the_day` in `burro_pipeline.travel.transxchange`, on the file as `Inputs` hands it over for the use `routing` |
| Time the journeys to a place | `Trains(...).to(place)` in `burro_pipeline.travel.timed`, then `timed_from` each home |
| Place the homes | `spine.build` and `centres.build`, as every measure does |
| Say which station a home is nearest | The stops of `connected.stops_round`, by `is_underground_or_dlr`, `is_a_railway_station` and `is_a_tram_stop` |
| Make the estimate | `estimated_minutes` and `band_against` in `burro_core.estimate`, on the release |
| Roll up to an area | `weighted_lower_median` in `burro_pipeline.travel.roll_up` |

The steps were driven by scripts in a scratch folder, which hold the names of the seven places and a row for every area. They are in no repository. A run takes under a minute once the file is read, and reading it takes 15 seconds.
