# 0027. A journey is estimated from distance until a timetable is held, and is said to be an estimate

Status: accepted, 2026-09-24. The founder asked for it. Its numbers are a first guess, for the founder to adjust: the last section says which.

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
| The three bands | Likely within: the estimate is at least 5 minutes under the limit. Likely beyond: it is more than 10 minutes over. Borderline: anything between |
| A firm limit | Leaves out only the areas that are likely beyond it, under a reason of its own, `commute_likely_beyond`. What is borderline stays in the list |
| A flexible limit | Leaves no area out. A journey that is likely within its limit counts in full, one that is borderline for a half, and one that is likely beyond for nothing |
| What is served | The band, the limit, and the line "Estimated from distance, not from a timetable." The estimate in minutes is served nowhere |
| Where it is worked out | In core, for a search, from the release. It is a pure function of the two, so the same search gives the same answer. No release holds an estimate |
| Where the numbers are | In one place, `estimate.py` in core, each named. Route 11 serves them as `journey_estimate`, for the page of methods |
| When a time is held | The time takes the place of the estimate. A release that holds a time for a journey never has it estimated |

A build names the stations of London as places to reach, from the file of stops, so that a person can name one. A release that names places and has routed no journey is a preview, and says so on every answer (ADR 0017).

The engine is 1.13.0.

## Consequences

- **A person who names a workplace gets an answer.** The areas are put in three bands, and a firm limit leaves some out.
- **The answer is rough, and says so.** A straight line knows nothing of lines, of changes, of a river with no crossing, or of how often anything runs. Two places the same distance apart are estimated the same. So the bands are wide, a firm limit leaves out only what is well beyond it, and no card gives a time.
- **An estimate follows distance from the place.** For a workplace in the centre it follows distance from the centre, which a person could have guessed. It says little that is new until a timetable is read.
- **An estimate may be wrong for one area and right for the next.** An area beside a fast line is nearer in time than its distance says, and one across a river with no crossing is further. Nothing on a card says which.
- **A journey to a place that is no station cannot be asked for yet.** A build names the stations. A workplace, a school or a hospital that a person names is asked about as any place the release does not hold.
- **The fit of an area rests on a band.** Areas of one band are level on the journey, and the rest of what counts puts them in order.
- **Rule 7 gains a clause** that points here. Nothing else may be estimated without a decision record of its own.

## What would change it

| If | Then |
|---|---|
| The founder has timed some journeys and the bands are wrong for them | Change the numbers in `estimate.py`, and bump the engine. Nothing else moves |
| A build holds journey times | The estimate goes, for every journey that has a time. `homes_at` may stay: nothing else reads it |
| People read a band as a promise | The bands are said more plainly, or a firm limit leaves no area out on an estimate |
| A place that is no station must be reached | The places are widened, under the licence of what names them. The estimate is the same for any place |
