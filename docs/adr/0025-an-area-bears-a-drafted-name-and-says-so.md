# 0025. An area bears a drafted name, and says that it is a draft

Status: accepted, 2026-09-24. The founder asked for it. Four readings of it are the founder's to confirm: the last section says which.

## Context

Every area of a build of London is a census area, under the label the statistics office gives it: a borough and a number. Nobody knows a place by that, and the founder judges the product by what comes back when a sentence is typed.

[The areas design](../design/london-data-areas.md) names London's areas by another road: a draft of about 490 neighbourhoods, each a set of census output areas under a name a publisher writes, which a person reads at the review desk before it ships. That draft exists. Its names were to reach a release only once its borders were checked, and a build kept to the rule that an area is given no name until then.

On 2026-09-24 the founder decided that one official publisher is enough for a name ([ADR 0022](0022-one-official-publisher-is-enough-for-a-name.md)), and asked that the areas of a build bear names now, as drafts that say so.

## Decision

**An area of a build bears the name of the drafted neighbourhood that holds most of its output areas, and says that the name is a draft until a person has decided it.**

| | |
|---|---|
| Which name | The name of the drafted neighbourhood that holds more of the area's output areas than any other. The draft gives an output area to the neighbourhood whose seed is nearest along the roads, so it is the name nearest to where most of the area's homes are |
| Counted in | Output areas, and not homes. The licence registry gives no count of homes for naming a place, and an output area is drawn to hold much the same number of homes as the next |
| A name | One that a publisher's record writes letter for letter. No name is coined, respelt or supplied from memory |
| No name | An area none of whose output areas lies in a neighbourhood that gives a name keeps its publisher's label |
| Two areas of one name | Each says its borough. Two of one borough each add the side they lie on, as "north" |
| The label | Stands beside the name, smaller, wherever the name is shown. The id and the slug of an area are still made from it, so neither moves when a name is decided |
| A draft | Every name, until a person has decided it at the review desk. The release says which of the two each name is, and who wrote it |
| What a person decided | Takes the place of the draft. The build reads the desk's own files, where they were compiled from the draft |
| What the build reads | Three files of the draft, each named in the lock by its hash. A name rests on the publisher's file that writes it, which must be a file of the build |

What was not taken:

| Way | Why not |
|---|---|
| Wait until the borders of the draft are checked, and rank the drafted neighbourhoods themselves | It is the design's own road, and it is some weeks of a person's time. Every measure of a build is worked out for census areas today |
| Give an area the name of the place whose point lies nearest its middle | It is a second way of naming beside the draft's, and it puts names the draft weighed lightly over well-known ones |
| Serve only the names that stand by the rule of ADR 0022 | 126 of the 488 drafted names wait at the desk, and an area that lies in one of them would bear the name of a neighbour or none |
| Pass over a name that the draft marks as perhaps a street or a building | The mark is blunt. It falls on names that are wrong and on names everybody uses, and turning a name down is a person's decision |
| Put the borough in the name | Every sentence that says the name would say the borough twice |

## Consequences

Counted on the build `lon-2026-09-24-96`. The page on it, which is in no tracked folder, gives every area.

- **Every result reads as a place.** All 1,002 areas bear a name, under 458 names. 312 of those names are borne by two areas or more, because a neighbourhood is larger than a census area, and 806 areas say a side.
- **A name may be wrong, and nobody has read it.** A draft is the work of a method. It gives an area at the edge of a neighbourhood the name of the neighbourhood next door, and it carries the names of the draft that look like a street or a development. Each says that it is a draft, and the page of methods says how it was chosen.
- **The design's promise that a person reads every name before it ships is set aside for a preview.** A preview is for the people who build Burro and is never launched (ADR 0017). Whether a drafted name may be shown in a finished release is not decided here.
- **A release may now cite a source of names.** `neighbourhoods.json` of a build that was given a draft cites the publishers that write its names, and is dated as the newest of their files. The licence gate is asked about each for `gazetteer`, as before.
- **A search by name finds an area.** The name alone is another name of every area that says a side, so a search for it finds them all, and no words of a sentence are read as one of them. A name that one area alone bears is read in a sentence as the name of an area always was, so "not in" before it leaves the area out.
- **A build that is given no draft is as it was.** Every area is under its label, and nothing is said of a name.

## What would change it

| If | Then |
|---|---|
| The founder wants a name that waits at the desk kept out until it is read | A neighbourhood gives a name only where `areas.csv` says `named_by_rule` or a person chose it. An area that lies in any other bears the name of the next, or keeps its label |
| The founder wants a name that may be a street or a building passed over | The build reads the draft's marks, and passes over a name that carries that one and that no person has chosen |
| The founder finds that two areas that say the same side confuse | The nearer of the two to the middle says "central". 16 areas of the build say what another area of their borough says |
| The founder wants the slug of an area made from its name | A slug is an address that lasts, so it is decided once: after the names are read, and not from a draft |
