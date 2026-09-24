# 0010. One contract, and a synthetic release to build on

Status: accepted, 2026-09-23. Two points marked below are judgement calls for the founder to confirm. Three more have been decided.

## Context

The backend has three parts: the ranking engine, the release builder and the API. They were built one after another, each by someone who had not seen the others' code. There was no real data to build on: no source had been ingested, no journey had been routed, and no model key existed.

## Decision

- [`docs/design/contract.md`](../design/contract.md) is the one description of how the three parts fit. If code and contract disagree, one of them changes in the same commit. What a builder had to decide alone is written into the contract where it applies, not kept in a list beside the code.
- Dependencies point one way: `burro_pipeline → burro_core ← burro_api`. The pipeline and the API never import each other. They meet at the release folder.
- `open_release` in core is the only thing that decides whether a release is valid. The pipeline and the API each read the bytes and call it.
- A release folder holds the release's files and nothing else. A stray file, a hidden one included, is refused. One file is excepted: a `.DS_Store`, which the pipeline's reader and the API's loader both leave out and never open. See the table of what was decided.
- The backend runs on a synthetic release until real data is ingested. It replaces the one-borough fixture the plan names. Every name in it is made up, every coordinate is in open sea, every id begins `syn-`, and `synthetic: true` travels to every response. It is generated, committed, and rebuilt byte for byte by a test.
- The character of each synthetic area is set by hand and the seed only adds noise, so a test can say which area a spec should find and why.

**To confirm**

| Call | Why it was made | To reverse it |
|---|---|---|
| The manifest names no engine range | A release never changes, so it must not have to be rebuilt because the arithmetic moved. `rank()` records both | Add the range to the manifest and a rule to `parse_release` |
| The release holds no population figure | Nothing after the pipeline needs one, and a count of residents that is not there cannot be ranked on or shown | Add the field to `neighbourhoods.json` |

**Decided**

| Call | Why it was made | Decision |
|---|---|---|
| `university_proximity` has one direction | "Far from a campus" is a way to ask for fewer students, which ADR 0006 refuses in words | 2026-09-23: it keeps one direction, and the rules refuse the request in words. ADR 0006 says so |
| A stray file is refused, a hidden one included | A folder that holds anything else is not the release that was written | 2026-09-23: a file named exactly `.DS_Store` is left out by the pipeline's reader and by the API's loader, because a Mac leaves one in any folder that has been opened in a window. Every other stray file is still refused. `open_release` is unchanged and would refuse one it was handed; it is the two readers that do not hand it over |
| A journey may take 0 minutes | It is a valid time, and the map can put a place at the middle of its area | 2026-09-23: no journey in the synthetic release is shorter than 2 minutes. The floor is in the generator. Core still reads a 0 as it stands |

## Consequences

- Real data, real journey times and a live model replace the synthetic ones without changing the code around them: a pipeline step ends in `write_release`, and everything that reads a release stays as it is.
- The contract is long. It is the price of three parts that fit without their builders meeting.
- Opening the fixture folder in a file browser can leave a `.DS_Store` there. The pipeline's reader and the API's loader both leave it out, so the service starts on any folder that `burro-release check` passes. Any other hidden file is refused by both, and the refusal names the file.
- "Every name in it is made up" is as true as the people who read the names could make it. Three turned out to be real places and were replaced on 2026-09-23. The same day every name was looked up in one encyclopaedia: two more of the city's names and three of its aliases were found to be real and were replaced, with no id moved, and so were nine names in the releases the tests build by hand. No gazetteer has been consulted, so the rest are made up as far as an encyclopaedia can say, which is not far for a street or a hamlet. The contract's sections 2.9 and 13 say what was done and what is left to do.
- Nothing about the synthetic city is a claim about any real place, so no ranking seen on it says how the product will feel on London.

## What would change it

The first real release. The synthetic one stays as the test fixture; the default the service starts on becomes a setting.
