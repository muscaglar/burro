# 0024. An area with no figure for what was asked for stands below every area that has one

Status: accepted, 2026-09-24. The founder decided it. One reading of it is the founder's to confirm: the last section says which. **Amended on 2026-09-27**, once the founder had walked the website a third time: a result of the website says which figure it lacks in a line of two words, and in a sentence under its working. The order, the fit and the engine are as they were. See "Amended, 2026-09-27", below.

## Context

Missing data is never filled in (rule 7). Where an area has no figure for a thing that counts, the thing is left out for that area and its weight is shared among the rest. So the fit of such an area says nothing of the thing, for good or ill.

That put an area first for the very thing it had no figure for. Asked for period homes and clean air, the first results of a build held no figure for one of the two. The card said how many things the fit rested on, and a line under it named what was missing. The area still stood first.

## Decision

**An area with no figure for a thing that was asked for stands below every area that has one.** Its card says which figure is missing. It is never left out for it, and never scored as nought.

| | |
|---|---|
| The order | First the areas with a figure for all that was asked, in the order of their fit. Then the areas with none for some of it, in the order of theirs. The id decides between equal fits, as before |
| The fit | Worked out as it was: the thing is left out, and the rest count for more. So a fit may be higher below the line than above it |
| What was asked | Every journey, a budget, every vibe, and every measure that is not a usual setting. `asked_for()` in core's `rank.py` holds it |
| A usual setting | A measure the tenure weighs by default, which stands the way its default runs, at the weight of the default or at what that gives way to once a wish is applied. Nobody asked for it, so its want moves no area |
| Who set a weight | It is never read. Ranking is a function of the spec in its canonical form, which holds no record of who set what (ADR 0002). A usual setting is told by its weight |
| An area with too little data | As before: an area with a figure for under half of what counts is not ranked, and is listed apart |

The engine is 1.12.0.

## Consequences

- **A wish can no longer be answered first by an area that cannot answer it.** That is what the founder asked for.
- **The list is no longer in the order of the fit from top to bottom.** It is in that order down to the last area with every figure, and again below it. The website sorts nothing, and the card of an area below the line says what it lacks, so the reason is on the page.
- **An area at the edge of the data falls further.** A measure that the edge of London has no figure for, such as the distance to a station that lies outside the file, puts an area below the line whenever a person asks for that measure by name. Where nobody asked, it moves nothing.
- **A cost that is not known now counts against an area** in a search that holds a budget. ADR 0021 kept such an area in the list with its cost not known. It is still kept, and still says so. It now stands below every area whose cost is known.
- **A person who sets a slider to the very weight nobody chose has, to the engine, chosen nothing.** The website marks the setting as theirs, and the engine moves no area for it. The two agree on every other weight.

## Amended, 2026-09-27: what a result says of a figure it lacks

The founder walked the website a third time, late on 2026-09-26, and asked for less on a result: "we need the info to be title of what was asked for, the visual gauge, and where relevent, the approx data call out". [0046](0046-a-result-shows-what-was-asked-for-as-a-name-and-a-gauge-and-the-source-of-every-figure-stands-under-its-working.md) records what a result shows since.

| This record says | Now |
|---|---|
| Its card says which figure is missing | It does, in fewer words. On the website the result of such an area has a line for each thing that was asked for and has no figure, by the name of the thing, with the two words "no data" beside a step that holds nothing. Of a vibe, its gauge is drawn with five empty steps and no peg, which is neither nought nor the middle. The sentence that names what is missing, and the service's own sentence for each thing, are under the working of the result |
| The fit of such an area | Worked out as it was. It says "approx data" beside it on the result, since it rests on part of what counts, and what it is based on is under the working |
| It is never left out for it, and never scored as nought | As it was. Nothing of the ranking was changed |
| The website sorts nothing, and the card of an area below the line says what it lacks, so the reason is on the page | The reason is on the page still, in sight and with nothing pressed: the line that says "no data" names what the area lacks |
| A usual setting that has no figure | It has no line on a result, since nobody asked for it. It is named under the working, as what nobody chose |
| Why a higher fit stands under a lower | **Since later on 2026-09-27 the result says so under its fit**, in one sentence: "This area is listed lower because it has no data for something you asked for." Seen in a browser that morning, after a sentence of seven things: fits of 54, 44, 35, 53 and 34, and nothing that said why. The website says it of an area that has no figure for a vibe, a measure or a budget that was asked for, or no time for any of its journeys, by the ranking it was given: the service does not yet say which areas stand below the line, and the website sorts nothing. The list of results and the table of all areas each say that they are in the order of the ranking: the table said "in order of fit" |

**What it gives up.** Two words say less than a sentence did. The sentence said that the person had asked for the thing, that Burro has no figure for it in the area, and that the fit leaves it out. "No data" beside the name of the thing says that there is none, and leaves the rest to the working.

What holds it, beside the list of results in `apps/web/src/components/ResultList/`: `test_a_vibe_that_was_asked_for_and_has_no_figure_has_its_line_on_the_result_with_an_empty_gauge_and_says_no_data`, `test_what_nobody_chose_and_has_no_figure_has_no_line_on_a_result_and_is_named_in_its_working`, and `test_journeys_that_do_not_count_because_none_has_a_time_are_said_on_the_result_to_be_not_known_and_in_its_working_why`.

## What would change it

| If | Then |
|---|---|
| The founder meant that a usual setting counts as asked for | `asked_for()` returns every component. An area that lacks the distance to a station, which a search starts with, then stands below the line in every search |
| The founder wants an area below the line to be marked in the list, and not on its card alone | The API serves, for each area, whether it lacks what was asked. It is a field of the contract, and the clients follow |
| People read the second run of fits as a fault | The list is cut at the line, and the areas below it are listed apart, as the areas with too little data are |
