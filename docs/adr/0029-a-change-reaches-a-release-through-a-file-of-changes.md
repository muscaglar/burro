# 0029. What a person decides at the panel reaches a release through a file of changes

Status: accepted, 2026-09-25. The founder asked for the panel, and said what it is for. How a change reaches a build was proposed here, and the founder accepted it the same day: the last section has their words. Builds on [0002](0002-deterministic-core.md), [0006](0006-rank-places-not-residents.md), [0013](0013-vibes-are-the-centre.md) and [0026](0026-the-chains-in-a-place-are-measured-by-a-table-of-tiers.md).

## Context

The founder decided that vibes are opinionated, and that a person reviews and adjusts their weights later ([0013](0013-vibes-are-the-centre.md)). Of the panel the founder said:

> This will act as the master admin panel/audit/relabel for the data we present etc

And of how it is built, with the spelling put right:

> Let's not over-engineer or over-complicate.

A recipe and a name were code. A release repeated each, and core refused a release that differed from its own by a hundredth. So to adjust a weight was to change core, the contract, the fixture and every recorded answer, in one change that only a programmer could make.

## Decision

**A change is a line in a plain file. A build reads the file, and the release carries what was decided. Nothing a person does at the panel changes what is served until a build is made from it.**

| | |
|---|---|
| The file | One line of JSON for each change, with who made it, the day, what stood before, what stands now, and why in the person's words. A line is never changed and never removed: to take a change back is a line too. [The design](../design/panel.md), section 3 |
| What a build does | It is given the file by name. It names it in the lock by its hash, applies the lines that stand, and says in its record which it applied. With no file it is byte for byte what it was |
| What a hosted build does | It is given the one place the desk publishes the founder's file to. Where the repository tracks a file there it takes it as a build by hand does, and where it tracks none it builds as it did. It never reads a file the repository does not track, and no step of a run is left out for want of one ([0030](0030-a-release-is-kept-approved-by-its-lock-and-carried-in-the-image.md)). Added 2026-09-25 |
| What a release may carry | A vibe whose hundredths, name, ends and lines of what it cannot see are not core's. A measure whose label is not core's. Nothing else of either may differ |
| The table of tiers | A chain that was moved to another tier, added or taken out is laid over the table for the build that reads the file, and the measures of the chains are worked out by it. The file of the table is what a build starts from ([0026](0026-the-chains-in-a-place-are-measured-by-a-table-of-tiers.md)) |
| What holds it | `checked_recipe()`, which every recipe of core is held to, is what a recipe of a release is held to. No part is added, taken out or turned round |
| Ranking | Still a function of a search and a release ([0002](0002-deterministic-core.md)). `rank()` reads what a release holds, as it did |
| Who is built from | The founder's file. Another reviewer's change is a proposal, shown beside the founder's and never built |

## Consequences

- **Two releases of one catalogue version may place an area in two bands.** Each says its own recipe, and a page shows the recipe of the release it is served from. The lock of a release names the file of changes it was built with.
- **Core's recipe is what a build starts from, and no longer what every release holds.** A change to core's own recipe is still a change to the catalogue, and bumps its version.
- **A change that was decided against a recipe that has since moved is never applied.** The line says what stood before. Where that is not what stands, the build stops and names the line.
- **The reader still answers to core's names.** A vibe that a release renames is asked for by the name core gives it, and shown under the name the release gives it.
- **A name a person gave is held to the words no sentence may say.** It holds no figure, no word of the verifier's lists, and no word for a group of people.

- **The file can be written by hand, so the panel's limits protect nothing.** What a person may change is held by the reader of the file, by the build and by core, and the panel asks them. A build takes the founder's file alone, and only as the repository holds it at the commit that is checked out. A release says in its manifest which file it was built with, and core serves it only beside a lock that names that file. [The design](../design/panel.md), section 9, lists what is refused, by whom, and what cannot be told.

## What would change it

| If | Then |
|---|---|
| A person should be able to add a part to a recipe, or take one out | It is a change to the catalogue, in code, as today. The rules of [0006](0006-rank-places-not-residents.md) are held where a recipe is written |
| The file should hold a figure | It never does. A figure is a publisher's. A person flags one. To leave one out of a build has a line in the file and is not built: it needs a state of its own in the evidence |
| A number set by judgement should be moved | The panel lists each and changes none. [The design](../design/panel.md), section 6, says what each would take |
| A second reviewer's change should be built | The founder keeps it as their own, which is a line of the founder's |

## Accepted, 2026-09-25

This record and [0030](0030-a-release-is-kept-approved-by-its-lock-and-carried-in-the-image.md) were put to the founder together, as the second of a list of questions: whether the two designs are accepted. These are their words:

> 2. Yes.

Nothing of the design changed with it, and no code did.
