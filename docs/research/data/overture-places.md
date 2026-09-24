# Overture Places in London: what a first look found

Written 2026-09-23. A dated snapshot, not a source of truth.

This was the first time a real data file was opened for Burro. It measured one source, Overture Maps Places, registered as `overture-places`. The licence gate was asked before each download and allowed it. Nothing downloaded is in this repository, and no figure here is a fact about a named neighbourhood. None may be shown to a user.

A second person ran the measurements again and recounted about 130 figures with code of their own. Every figure matched or differed by rounding. What follows keeps their corrections.

## What was read

| | |
|---|---|
| Release | `2026-09-23.0`, the newer of two on the public bucket |
| Area | A box round London of about 2,780 km². A box is not the boundary: it takes in land outside London |
| Read over the network | About 128 MB of 11 GB, in about five minutes |
| Places in the box | 496,244 |
| Of a kind Burro cares about | 99,920, one in five |

## Who gave the records

| Upstream source | Share | Licence |
|---|---|---|
| Meta | 52.9% | CDLA-Permissive-2.0 |
| Microsoft | 24.1% | CDLA-Permissive-2.0 |
| Foursquare | 18.8% | Apache 2.0, with a notice to carry |
| AllThePlaces | 3.9% | CC0 |
| Three others | 0.3% | |

Every record names exactly one upstream source, so records can be told apart by licence, as the registry asks.

## What the file can and cannot say

| Question | Answer |
|---|---|
| Is the confidence score a usable filter | For Meta's records only. Foursquare gives one value, 0.77, for every record |
| Are there duplicates | Few: 0.17% by exact name within 50 m |
| Can a closed place be told from an open one | No. The field for it is empty for 99.87% of records |
| Can the age of a record be told | For Microsoft and Foursquare only. 62.8% of Microsoft's records are dated 2019 or before |
| Is a brand given | For 8.8% of records, and 17.9% of gyms |
| Does it change between releases | In one month 0.72% of records went and 2.83% were new |
| Is there a field for price, rating or opening hours | No |

## What it is good enough for

- Deciding what this source cannot carry: GP surgeries, pharmacies as a register, markets, gym operators and tiers, which places are independent, and anything about opening or closing.
- A first value for the confidence floor: 0.7 for Meta's records and none for the others, to be set again against a register.
- Sizing the ingest step: how much is read, how long it takes, and that the libraries it needs install as the project requires.

## What it is not yet good enough for

| Finding | Why it matters |
|---|---|
| Counts track how much is there, and the centre | Within 15 km of the middle of the box, places to eat and drink rank almost exactly as the count of all records does (rank correlation 0.96). A vibe built on it may only say how central an area is |
| A zero cannot be trusted | Cover thins with distance from the centre for every kind. A gap cannot be told from a place with none |
| Kinds hold things that are not the kind | Half the records under theatre are stage schools by their names. Half the community halls are scout groups from one feed |
| One institution has many records | Counts of hospitals, universities and stations are not believable |
| A small area's figure moves between releases | In one month the count of gyms within reach moved by a fifth or more in about one cell in five |
| One record can fall in two figures | Some venues count as both culture and evening, and some shops as both food shops and places to eat |

## What must happen before any figure from it is shown

1. Official boundaries, so that figures are for London and for named areas, and not for a box.
2. A check of 20 areas against the food hygiene register, which has not been read.
3. Rules for each kind that match the kind and not its parent, checked by hand on a sample.
4. A rule for when a zero may be kept that does not keep nearly every zero.
5. A test that each figure says something that plain density does not.

Until then, no vibe rests on this source.

## Credit

Overture Maps Foundation, overturemaps.org. Records from Meta and Microsoft are under CDLA-Permissive-2.0, from Foursquare under Apache 2.0, and from AllThePlaces under CC0.
