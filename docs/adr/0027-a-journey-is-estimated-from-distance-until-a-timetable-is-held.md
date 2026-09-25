# 0027. A journey is estimated from distance until a timetable is held, and is said to be an estimate

Status: accepted, 2026-09-24. The founder asked for it. Its numbers are a first guess, for the founder to adjust: the last section says which. **Amended on 2026-09-25**, when the estimate was held against the timetables: no number was changed, and a change to one is recommended to the founder. See "Held against the timetables" below. **Amended again on 2026-09-25**: the founder decided that change, and a journey is called likely within its limit only where its estimate is 10 minutes or more under it. See "Decided, 2026-09-25" below.

## Context

A person names the place they must reach and how long the journey may take. No build of London holds a journey time: none has read a timetable. So a journey such as "at most 40 minutes from Chancery Lane" was answered "not in this data", and the one thing most people ask for first counted for nothing.

Missing data is never filled in (rule 7). A journey time that is made up is filled in. An estimate that says it is one, and claims no more than it knows, is not.

## Decision

**Where a release holds no journey time, a journey by public transport is estimated from distance. It is said as one of three bands against the limit the person set, never as a number of minutes, and it says that it is an estimate wherever it is shown.**

| | |
|---|---|
| What is estimated | A journey by public transport, from an area to a place the release names. By bike and on foot nothing is estimated |
| From what | The distance in a straight line between where the homes of the area stand and the place. Where the homes stand is the middle of the centres of population of the area's small census areas, which the release holds for each area as `homes_at` |
| How | A fixed part for the walk to a stop, the wait and the far end, and a part for each kilometre: 12 minutes, and 3 for each kilometre. Where the homes of the area are within 800 metres of a station of the Underground or the DLR, in a straight line, 2.5 for each kilometre |
| The three bands | Likely within: the estimate is at least 10 minutes under the limit. It was 5 until 2026-09-25. Likely beyond: it is more than 10 minutes over. Borderline: anything between |
| A firm limit | Leaves out only the areas that are likely beyond it, under a reason of its own, `commute_likely_beyond`. What is borderline stays in the list |
| A flexible limit | Leaves no area out. A journey that is likely within its limit counts in full, one that is borderline for a half, and one that is likely beyond for nothing |
| What is served | The band, the limit, and the line "Estimated from distance, not from a timetable." The estimate in minutes is served nowhere |
| Where it is worked out | In core, for a search, from the release. It is a pure function of the two, so the same search gives the same answer. No release holds an estimate |
| Where the numbers are | In one place, `estimate.py` in core, each named. Route 11 serves them as `journey_estimate`, for the page of methods |
| When a time is held | The time takes the place of the estimate. A release that holds a time for a journey never has it estimated |

A build names the stations of London as places to reach, from the file of stops, so that a person can name one. A release that names places and has routed no journey is a preview, and says so on every answer (ADR 0017).

The engine was 1.13.0 when this was decided. It is 1.14.0 since what is called likely within was widened.

## Consequences

- **A person who names a workplace gets an answer.** The areas are put in three bands, and a firm limit leaves some out.
- **The answer is rough, and says so.** A straight line knows nothing of lines, of changes, of a river with no crossing, or of how often anything runs. Two places the same distance apart are estimated the same. So the bands are wide, a firm limit leaves out only what is well beyond it, and no card gives a time.
- **An estimate follows distance from the place.** For a workplace in the centre it follows distance from the centre, which a person could have guessed. It says little that is new until a timetable is read.
- **An estimate may be wrong for one area and right for the next.** An area beside a fast line is nearer in time than its distance says, and one across a river with no crossing is further. Nothing on a card says which.
- **A journey to a place that is no station cannot be asked for yet.** A build names the stations. A workplace, a school or a hospital that a person names is asked about as any place the release does not hold.
- **The fit of an area rests on a band.** Areas of one band are level on the journey, and the rest of what counts puts them in order.
- **Rule 7 gains a clause** that points here. Nothing else may be estimated without a decision record of its own.

## Held against the timetables, 2026-09-25

Amended on 2026-09-25. The founder asked for the estimate to be checked, and it had never been. It was held against journeys timed from Transport for London's timetables of the Underground and the DLR, as fetched on 2026-09-24: to seven stations, from the 384 areas whose homes are nearest a station of either. [The page of the check](../research/data/journey-estimate-held-against-timetables.md) holds the method, every assumption with where it is from, and the counts. **No number of this record was changed** by the check, and the engine was as it had been. One was changed later the same day, by the founder: the next section.

What was found:

1. **It leaves out no area that the timetables put within the limit.** Of the 775 journeys that a firm limit of 40 minutes leaves out, none is timed within 40. Nor is any at 30 or at 45, and at 60 it is 1 of 193.
2. **It is short, so it keeps and promises too much.** The timed journey is 6 minutes longer in the middle: 2 to 11, by what is assumed of a walk and of the way through a station. Half of what a firm limit of 40 keeps is timed beyond 40, and so is 1 in 5 of what is called likely within. What is called borderline is beyond, nine times in ten.
3. **Three areas in five could not be checked.** 588 of the 1,002 areas, with 58.6 in 100 of London's homes, are nearest a railway station whose trains no file holds. In the founder's own search, 333 of the 422 areas left out were not timed. If the estimate leaves out an area that it should not, that is where it would be.

What is recommended, for the founder to decide:

| | Recommended | Why |
|---|---|---|
| Leaving out | As now: `BEYOND_BY` stays 10 | Nothing that is timed within 30, 40 or 45 minutes is left out |
| What is promised | `WITHIN_BY` from 5 to 10 | At 40 minutes what is called likely within is then timed beyond 6 times in 100, where it is 19. Nothing more is left out, and of an area that cannot be checked it only says less |
| The fixed part | Not moved alone | The timed journeys ask for about 18 to 22 minutes where it is 12. Moved alone, it leaves out a quarter more areas in the founder's own search, most of them areas that were not timed. With `WITHIN_BY` at 4 and `BEYOND_BY` at 16, a fixed part of 18 says of every area what the two rows above say |
| A number by the line a home is nearest | None | It fits no better on the areas it was not fitted on |
| When a build holds a time | The time takes the place of the estimate, as this record says | It is the one thing that sees a change of trains, and whether a line runs to the place |

The numbers in core are the founder's to change. The first row of the last table says how.

## Decided, 2026-09-25: less is promised

What is recommended of what is promised, the second row of the table above, was put to the founder as the first of a list of questions: widen one number, `WITHIN_BY`, from 5 to 10. These are their words:

> 1. Yes

| | |
|---|---|
| What changed | `WITHIN_BY` is 10. A journey is called likely within its limit only where its estimate is 10 minutes or more under it |
| What did not | `BEYOND_BY`, the fixed part and both rates are exactly as they were |
| What a firm limit leaves out | What it left out before, and nothing more: an area is left out where its journey is likely beyond the limit, and that rests on `BEYOND_BY` alone. A test holds it |
| What became of a journey 5 to 10 minutes under its limit | It was called likely within, and is called borderline. Under a firm limit it stays in the list. Under a flexible one it counts for a half, where it counted in full |
| Why | Held against the timetables, what was called likely within 40 minutes was timed beyond them 19 times in 100. With the number at 10 it is 6 in 100, on the areas nothing was fitted on |
| What is still not known | The estimate was held against timetables of the Underground and the DLR. It could not be held against trains: no file that is held has them, and three areas in five are nearest a railway station. Of those it only says less than it did |
| Where it is said | The page of methods says what likely within means, from the number core serves, and says what the estimate was and was not held against |
| The engine | 1.14.0 |

The other rows of what was recommended stand as they were: nothing else was decided, and nothing else was changed.

## What would change it

| If | Then |
|---|---|
| The founder has timed some journeys and the bands are wrong for them | Change the numbers in `estimate.py`, and bump the engine. Nothing else moves |
| A build holds journey times | The estimate goes, for every journey that has a time. `homes_at` may stay: nothing else reads it |
| People read a band as a promise | The bands are said more plainly, or a firm limit leaves no area out on an estimate |
| A place that is no station must be reached | The places are widened, under the licence of what names them. The estimate is the same for any place |
