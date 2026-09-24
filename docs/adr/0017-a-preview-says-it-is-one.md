# 0017. A preview says it is one, and states no source for what it does not hold

Status: proposed, 2026-09-23. It changes the contract, so it is the founder's to approve. It settles a point [0016](0016-geography-behind-a-measure.md) left open.

## Context

The first real build holds areas, outlines and a few measures for all of London. It holds no journey, no cost, no place to reach, no station and no vibe ([the plan](../design/london-data.md), milestone M1). The founder is to see it on the website before any of those exist.

Two things stood in the way.

1. **The contract asked for a source that does not exist.** `travel.json` and `stations.json` each had to name at least one source and a date, whatever they held. The first build has read no timetable and no list of stations. [0016](0016-geography-behind-a-measure.md) saw this and left it to the contract's owner.
2. **Nothing said that a release was unfinished.** A release said whether it was made up, with `synthetic`. The first real build is not made up, so it must say `synthetic: false`, or a real figure would be shown as invented. It then said nothing else, and read as a finished release.

## Decision

**A release says whether it is a preview.** `preview` is a field of the manifest, beside `synthetic`. It is true for a release that is not finished. Every response of the API carries it, in `meta` and in the header `X-Burro-Preview`, errors included.

| | `synthetic` | `preview` |
|---|---|---|
| The synthetic release | true | false |
| The first real build | false | true |
| A release that is launched | false | false |

**A preview states no source for what it does not hold.** In `travel.json` and in `stations.json`, `source_ids` may be empty and `as_of` may be `null`. Core refuses it unless all three hold:

- the manifest says `preview`
- the file holds nothing: no destination, or no row
- the source and the date are both left out.

Everything else is as it was. `neighbourhoods.json` always states its sources. A finished release states every source. No fact is made from a file that states none.

**Amended on 2026-09-24.** `preview` was taken on the release's own word. A release with no journey, no cost, no station and no place to reach passed as finished, if its empty files named a source. [0018](0018-a-real-release-is-served-with-its-evidence.md) closes that: a release that holds none of these says it is a preview, or core refuses it.

What was not taken:

| Way | Why not |
|---|---|
| Name a source the build did not read | It is making a source up. A credit for a timetable would then stand on the sources page of a release that holds no journey |
| Let a release leave out a file | It changes what a folder holds, and every reader of one. An empty file already says "nothing is here" |
| Say preview with `synthetic: true` | The figures are real, and a person must not be told they are made up. Rule 13 has a mirror: real data never passes as made up |
| Say nothing, and show it to nobody | Care is not a rule. A flag on every response is one |

## Consequences

- The first real build passes `open_release` and `burro-release check` with nothing invented.
- A client must show `preview` as it shows `synthetic`. The website does: it shows a banner on every page built on a preview, and as soon as any answer says its release is one. The app carries the flag in its models. Whether it shows it was not looked at.
- A journey asked of a preview is refused, because the preview has no place to reach. A budget is said to be missing. Where a budget is most of what was asked for, no area is ranked: too little of the wish can be tested (contract, section 6.6).
- `cutoff_minutes` must still be given by a release that routed nothing. The first build writes the contract's own numbers. That is open: contract, section 13.
- `schema_version` is still 1. That is open too: contract, section 13. **Amended on 2026-09-24**, when the vibes were joined with the first real builds: the schema is at version 2, which holds `preview` beside the way gritty is built. A preview carries the vibes core holds, with gritty as land use, and places an area on a vibe only where 60 in 100 of its recipe is measured. A first build does so for one vibe, Homes, and says that it rests on two of its three parts.
- The API serves a preview to whoever can reach it. Nothing in the service keeps one from the public: the address it listens on does, which is the machine's own unless somebody sets another.

## What would change it

- A reason to show a preview to people outside. The flag would then need words on the screen that they can act on.
- A third state. If "for closed testers" comes to mean something other than "preview", a flag of two values is too few.
