# 0016. The geography behind a measure is registered for scoring

Status: proposed, 2026-09-23. The registry change it records is the founder's to approve. Nothing was downloaded and no publisher's page was opened for it.

## Context

The first real build carries five measures for all of London: flats, homes built before 1919, homes per hectare, transport noise and nitrogen dioxide ([the plan](../design/london-data.md), section 4).

A figure is worked out from more than the file that gives it its name. Each of the five also rests on geography:

| Measure | The publisher's table | The geography it is worked out on |
|---|---|---|
| Flats, homes built before 1919 | `voa-council-tax-stock-of-properties` | The lookup. Households by output area, from `ons-census-2021-housing-tables`, as the weight where an LSOA is shared between areas |
| Homes per hectare | The same | The same, and the land area of each LSOA, from `ons-lsoa-2021` |
| Transport noise | `mhclg-iod-2025-underlying-indicators` | The lookup and the weight |
| Nitrogen dioxide | `defra-pcm-background-air` | The lookup and the weight. The centre of each output area, from `ons-oa-pwc-2021` |

The lookup is `ons-oa21-lsoa21-msoa21-lad22-lookup`.

`write_release` asks the gate for `scoring` for every source a catalogue row names. The three tables and the housing tables are registered for it. The lookup, the centres and the LSOA boundaries were registered for `cells`, and for `gazetteer` or nothing more. So the gate refused the first build, unless a row left its geography out.

The plan offered two ways through:

1. Add `scoring` to the geography sources a measure is worked out from.
2. A rule in the contract that a source registered for `cells` may stand behind a catalogue row.

## Decision

**The first.** `ons-oa-pwc-2021`, `ons-lsoa-2021` and `ons-oa21-lsoa21-msoa21-lad22-lookup` are registered for `scoring`. Each entry says what it does in scoring, and that no column of it is a measure in its own right.

Why not the rule in the contract:

- The gate asks one question: is this source registered for this use. The rule would make one use stand for another. That would hold for every source registered for `cells`, now and later, with nobody reading the entry.
- The registry has done it this way before. `ons-postcode-directory` is registered for `scoring` "only because it places postcode-keyed features into cells".
- It is three lines in one file. The rule would change the contract, `write_release` and its tests, for the same result.

What makes it honest:

- **A row names every source behind its figure.** The lookup, the weights, the centres and the boundaries are named beside the publisher's table. A row that named the table alone would pass the gate and hide what the figure rests on.
- **No new evidence was needed, and none was claimed.** Each of the three entries already held the publisher's own licence page, `https://www.ons.gov.uk/methodology/geography/licences`, and its item record, read on 2026-09-23 by the people who wrote the entry. Nothing the entries record of the licence sets scoring apart from the uses they already had. No lawyer has read this ([0007](0007-no-solicitor.md)). A test holds the three entries to that evidence.
- **Nothing else was widened.** `ons-output-areas-2021` and `ons-msoa-2021` are unchanged, because none of the five measures is worked out from them.

**A source named only in `evidence.json`** is asked for the use of the file that holds the fact its row stands behind: `scoring` for a feature, a tag or a cost, `routing` for a journey, `display` for a station, `gazetteer` for a name or a boundary. Evidence has no lighter use of its own. A receipt records the one use the gate was asked for when a file was fetched. A release is asked again, for every use the file was put to. `check` asks it, of every file a row of evidence rests on, and names the row under `input_is_allowed`. `write_release` reads only the sources a release names, so until evidence travels inside a release, which is for the contract's next schema, the rule holds where `check` is run.

## Consequences

- The five measures can be built with every input named, and pass the gate.
- The credits the product must show do not change. All three sources already reached users.
- Being registered for `scoring` does not make a column rankable. The list of features in core still decides what can be ranked.
- A later measure worked out on another geography source needs `scoring` added to that entry, in a change that a person reads.
- The preview of the first build is drawn on 1,002 MSOAs. If its outlines are read from `ons-msoa-2021`, that entry needs `gazetteer`, which it does not have. If they are made by joining output areas with the lookup, nothing more is needed. This record does not choose.
- A release had to name at least one source in `travel.json` and in `stations.json`, even when it held no journey and no station. What the first build names there was left to the contract's owner. [0017](0017-a-preview-says-it-is-one.md) proposes that a preview names none.
- If the VOA file uses LSOA codes of 2011, a lookup from 2011 to 2021 is needed. None is registered, and nobody has read its page. The first build then carries noise and nitrogen dioxide alone.

## What would change it

Many sources that are registered for `scoring` only as geography. A use of their own, such as `weights`, would then say it better.
