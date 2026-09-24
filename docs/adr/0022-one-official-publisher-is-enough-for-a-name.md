# 0022. One official publisher is enough for a name

Status: accepted, 2026-09-24. The founder decided it. One reading of it is the founder's to confirm: the last section says which.

## Context

[The areas design](../design/london-data-areas.md) asked that the name of an area rest on two publishers, and left it to the founder whether one is enough if too few names reach two. The first whole draft of London counted it. Of 488 areas, two publishers write the name of 154, and one publisher writes the name of 333. One area has no name.

The second publisher could only be the Greater London Authority's town centres. Wikidata has no file, and the licence gate refuses the names of the House of Commons Library. The town centre file has no receipt, and its outlines are based on Ordnance Survey mapping, so the two are not independent. Asking for two publishers asked most names for a second opinion that no file could give.

At the review desk the question stood 613 times: once as a flag on every name that one publisher writes. One of the eight rules put to the founder said that it waited on the same answer.

## Decision

**A name that an official publisher writes for a populated place, at a point inside the area, is a name.** It needs no second publisher.

| Term | Means |
|---|---|
| An official publisher | A public body whose file is its own list of populated places, each with a point. Today that is OS Open Names. `OFFICIAL_PLACES` in `areas/draft_decided.py` lists the sources, and one is added only once the registry approves it for `gazetteer` |
| Writes the name | The label of the record is the name, letter for letter |
| At a point inside the area | The point of the record lies in the area as drawn. An outline that lies over the area is no point. A record that lies outside puts the name nowhere in it |

What follows from it:

| | |
|---|---|
| The flag for one publisher | It is raised only on a name the rule does not fit. Such a name is held to the design's first rule: two publishers, and one record that puts it inside |
| A name that stands by the rule alone | The name of an area that the rule fits, and that the draft has no mark on. `areas.csv` says `named_by_rule`. The desk makes no item of it, and asks about its border as before. `named_by_the_rule.csv` lists each, to skim |
| A name that is still read by a person | One with any mark of the draft, because a mark is a doubt this decision did not settle: a name that may say who lives there, a name in two places, a name that may be a street or a building, a point on the line between two areas. One in whose area a heavier name lies, or the name another area was grown from. One that an outline alone places. Every other name of an area, whatever writes it. One a person has answered before |
| A name still says how many publishers write it | No record is taken away. `areas.csv` names every publisher that writes each name, the evidence holds a row for each, and an item at the desk says it in a line. A page names the publishers that write a name, and no more |
| The eight rules | They stay the founder's to adopt at the desk. The first three each ask what this rule asks, and then more, so nothing is left for them to settle. Each rule says on its own screen what this decision has settled of it. The fifth leant on the first three: it now lets through another name alone, and leans on the fourth |

What was not taken:

| Way | Why not |
|---|---|
| Wait for a second publisher | It waits on a query nobody has written and on a licence nobody has saved. Neither would be independent of Ordnance Survey beyond doubt |
| Let any one publisher be enough | A town centre is the name of a shopping street, drawn as an outline. It names no populated place |
| Let the rule settle a name with a mark | The decision is about who writes a name. A mark is about something else, and the founder has not been asked about it |
| Put the rule to the founder again at the desk, as a ninth rule | It was decided. Asking twice spends the time the decision saves |

## Consequences

Counted on the draft of London as it was made again on 2026-09-24. The ground did not change: every output area is in the area it was in.

| | Before | After |
|---|---|---|
| Areas whose name stands with no person reading it | 0 | 362 of 488. One publisher writes 257 of them, and two write 105 |
| Areas the rule fits, and the draft has a mark on | | 101. Each is still read |
| Areas the rule does not fit | | 25: an outline alone places 24, and 1 has no name |
| Items in the queue of names | 783 | 421 |
| Hours in that queue, at 45 seconds a name | 9.8 | 5.3 |
| Names flagged for one publisher | 613 | 86 |
| Names flagged for anything | 674 | 267 |
| What the eight rules would settle | 438 names, 26 borders | 172 names, 26 borders. 240 names that the first three fitted stand already |
| Names a rule would have settled that a person now reads | | 26: 19 names of areas with a mark that asks nothing, 5 in whose area a heavier name lies, and 2 in whose area lies the name another area was grown from |

- **A person no longer reads every name before it ships.** The design held that one does. 362 names now ship on the word of one file and the absence of a mark. The marks are blunt: they see whole words and records, and know no place. A name that is wrong and carries no mark ships unread.
- **The border is still looked at.** Every area is an item of Borders under its name. The border of an area whose name stands says first that nobody has read the name, and to say so in a note if it looks wrong.
- **A name that stands can be turned down by hand.** Write its `area_id` and an answer in the file of decisions, and make the draft again with `--decided`. The desk cannot do it: it holds no item of the name.
- **The pace is a guess.** Nobody has timed a name. A checker who sat at the desk found about 12 seconds for a name that shows nothing to weigh, which would make the saving 1.2 hours and not 4.5.

## What would change it

| If | Then |
|---|---|
| The founder meant that the flag is lifted and every name is still read | Make the draft with `--read-every-name`. The rule then lifts the flag, no name stands by it alone, and the first three rules settle what they did before. It is the founder's to confirm which was meant |
| A second official list of populated places is approved for `gazetteer` | It is added to `OFFICIAL_PLACES`. The rule does not change |
| Wikidata or the names of the House of Commons Library arrive | More names say that two publishers write them. The rule does not change |
| The people test finds that residents reject names that stood by the rule | Every name is read again, as the row above |
