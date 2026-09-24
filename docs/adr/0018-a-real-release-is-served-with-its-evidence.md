# 0018. A release that is not made up is served only with its evidence, and says if it is unfinished

Status: proposed, 2026-09-24. It changes the contract, so it is the founder's to approve. It follows [0014](0014-evidence-first-and-census-figures-shown.md) and [0017](0017-a-preview-says-it-is-one.md).

## Context

Two checks were made of the first real build, neither by whoever built it. Each changed it after it was built and looked for what noticed. Four things did not.

1. **A figure could be changed and still be served.** The evidence held a row for every fact, and no row held the figure. Nothing on disk held the hash of the manifest, and nothing read the hash of the evidence or of the lock. A figure raised by 20, with the manifest made to agree, passed every check.
2. **The service never read the evidence.** The evidence stands beside the release and not in it, because core refuses a release folder that holds a file it does not know. So the service served a release with no evidence at all, and a measure that nobody had evidence for. The made-up release under real ids, with its flag flipped, was served as real and finished.
3. **A release was finished on its own word.** `preview: false` was taken as given. A release with no journey, no cost, no station and no place to reach passed as finished, if its empty files named a source.
4. **No figure was held to a range.** A share of 140 in 100 and a level below nought were served.

## Decision

**A build writes the hashes of what it built.** `hashes.json` stands beside the release, with the evidence and the lock. It holds the SHA-256 of the manifest, of the evidence and of the lock. The manifest holds the hash of every file of the release, so the three fix every byte.

**A release that is not made up is served only with its build beside it.** `open_served` in core takes the bytes of the release and of the three files beside it. It refuses a release that is not made up unless all three are there, the hashes are of this release, and each of the manifest, the evidence and the lock has the hash it was written with. The service and `burro-release check` both open a release through it. A made-up release is built from no file, and needs nothing beside it.

| Refused when | Rule |
|---|---|
| The hashes, the evidence or the lock is not in the folder beside the release | `real_release_has_its_build` |
| The hashes are of another release | `build_is_of_this_release` |
| The manifest, the evidence or the lock is not as it was written | `build_is_as_it_was_written` |

**The row of a figure holds the figure.** The row of evidence of a measure holds its value, and of a tag its score. `check` and `burro-release check` hold the release to it. `burro-release check` holds each row to the method and the one file the code names for its measure too, because two measures may cite one source.

**One file, or the file of each square.** Amended on 2026-09-24, with the second build, and proposed as the rest is. One file is too few for a product that its publisher cuts to squares of the National Grid, a file for each: a figure at the edge of a square rests on two. A measure that reads such a product says so where the code lists the measures of a build. Its row may rest on the file of each of several squares, never on one square twice, and never on a file of the source that the measure does not read. Every other measure is held to one file, as before. The other way was to fetch the product as one file for Great Britain, which needs a fetch and changes no rule.

**The check asks again, as things stand on the day it is run.** Amended on 2026-09-24, after two checks of the second build, and proposed as the rest is. With the hashes of a build made to agree, a checker changed a release in ways that every figure survived, and the check passed each. It now holds more:

| What was changed, and passed | What the check does now | Rule |
|---|---|---|
| The registry gated a source after the build, or withdrew the use it was put to | It asks the registry as it stands on the day, under the one rule of [ADR 0016](0016-geography-behind-a-measure.md): about every file a row rests on, for the use the figure is put to, and about every source the release cites that no such row rests on a file of, for the use of the file of the release that cites it. One fault is found once. Only an approved source stands behind a release | `input_is_allowed` |
| A percentile was moved, with its figure left alone. An area is ranked on its percentile | It works each percentile out again from the figures of the release, with core's `percentile_of` | `percentile_is_cores` |
| The raw value of a tag, its score, or the share of its recipe it rests on | It works each tag out again from those percentiles, with core's `tag_raw` | `tag_is_cores` |
| The share of an area that stands behind a figure | It holds the share to the row of the figure | `row_holds_the_coverage` |
| A receipt in the evidence was given another edition, address, size or hash under the same id | It holds a receipt to the lock by the whole hash and the size. Given the folder of receipts that were committed, it holds the receipt to the one committed for its file | `receipt_is_the_locked_file`, `receipt_is_as_committed` |
| The row of a tag named the method of a measure | It holds the row of a tag to the method of a tag, and to the files of the measures of its recipe | `row_names_its_method`, `row_rests_on_its_file` |
| The credit and the licence of a source in the manifest | It holds what the manifest says of a source to the licence registry | `credit_is_the_registrys` |

Core is not changed by any of these. The arithmetic is core's, and the check calls it.

**To approve a release is to commit its lock and its hashes.** Until a release is approved, nothing outside the build's own folder holds its hashes. A person who changes a release can then change its hashes with it. `burro-release check` still holds every figure to its row. Once the hashes are committed, a change shows in the history.

**Until a release is approved, only `burro-release check` is proof.** The service holds a release to `hashes.json`, which stands in the folder beside it and is signed by nobody. A checker rewrote it, and the service then served a figure raised by 20, the rows of two measures swapped, a nought where the publisher withheld a figure, a measure added with no evidence, and evidence with no rows. `burro-release check` refused each. So the service is run on a release only after `burro-release check` has passed on that folder, as it stands. Which of the two ways below closes this is the founder's to say.

**A release that holds no journey, no place to reach, no cost or no station is a preview.** Core refuses one that says it is finished: `finished_release_is_whole`.

**A figure is held to what its unit can be.** A percentage is from 0 to 100, and a figure of any other unit is not below nought. An outline lies round the point inside its area, and neighbours lie near each other, within half a degree.

What was not taken:

| Way | Why not |
|---|---|
| Put the evidence inside the release | The schema must move first, and another change in flight moves it. The folder beside the release needs no change to what a release folder holds |
| Have the service run the evidence check | The service never imports the pipeline. It holds the bytes to their hashes, and the pipeline checks what the bytes say. It is one of the two ways to close what is said above of the service. The other is to commit the hashes of an approved release, and have the service take them from outside the folder |
| Record in a receipt which square of the grid a file is of | Fetch alone writes a receipt, and no receipt carries the geography of its file yet. So the check cannot tell which square a figure lies on: see what is not held |
| Hold London to a box on the map | Every test builds a town under real ids, and draws it in open sea so that nothing made up is laid over a real street. A box would refuse them all. An area is held to the rest of its own release |
| Let a release with no journey leave `cutoff_minutes` out | It changes what the service serves and what the website draws. It is left open: contract, section 13 |

## Consequences

- The service needs the folder `ID-build` beside the release it serves. A release copied without it is refused when the service starts, and the refusal names the file that is missing.
- A release, its evidence and its lock never change once written. A correction is a new release.
- The evidence written before this decision holds no figure, and its hash differs. No release had been approved, so none is lost.
- The website shows a page only while every answer is of the kind of data the page was built on. A page built on made-up data, read while the service answers with real data, shows a notice and no figure, and the other way about.
- What is not held: the label, the outline, the cost, the journey and the station of an area have no value in their row of evidence. The hashes hold them, and nothing else does.
- What only committed hashes protect. With the hashes made to agree, both the service and `burro-release check` passed a release in which the names of two areas were swapped, so that each wore the other's figures, the outlines of two areas were swapped, half the areas were marked not to be ranked, and the sentence of a measure was changed to claim more than it counts. A changed label or polarity of a measure is refused, because core holds those. Nothing holds a name, an outline, which areas are ranked, or the sentence of a measure, until the hashes of the release are committed.
- The check cannot tell which square a figure lies on. For a measure whose product is cut to squares, a row may rest on any one or more files of the source that the measure reads. A row of an area on one square that named the file of another alone passed, and so did every row naming both. Every other measure is still held to one file. It is closed when a receipt says which square its file is of, or when the product is fetched as one file.
- A credit that the registry changes fails every release built before the change, until it is built again. That is meant: a release credits a source as the registry does on the day it is checked.

## What would change it

- A schema that holds the evidence inside the release. The three hashes would then go in the manifest, and core could refuse with no folder beside it.
- A store of approved hashes that the service can read. It could then refuse a release nobody approved.
