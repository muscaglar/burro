# 0024. An area with no figure for what was asked for stands below every area that has one

Status: accepted, 2026-09-24. The founder decided it. One reading of it is the founder's to confirm: the last section says which.

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

## What would change it

| If | Then |
|---|---|
| The founder meant that a usual setting counts as asked for | `asked_for()` returns every component. An area that lacks the distance to a station, which a search starts with, then stands below the line in every search |
| The founder wants an area below the line to be marked in the list, and not on its card alone | The API serves, for each area, whether it lacks what was asked. It is a field of the contract, and the clients follow |
| People read the second run of fits as a fault | The list is cut at the line, and the areas below it are listed apart, as the areas with too little data are |
