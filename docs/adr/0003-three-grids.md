# 0003. Three grids, one cell table

Status: accepted, 2026-09-23. Counts to be confirmed in phase 0b.

## Context

The research disagreed about the base grid. Census Output Areas nest exactly and follow real streets, but workplaces cluster where few people live, so they make poor destinations. Hexagons are uniform, but their centres can fall in a park. The routing engine processes one origin at a time, so the number of origins drives compute cost.

## Decision

| Layer | About | Used for |
|---|---|---|
| Census Output Area (2021) | 26,400 | Neighbourhood membership, census sums |
| LSOA population-weighted centroid | 5,000 | Where journeys start |
| H3 hexagon, resolution 9 | 16,700 | Where journeys end |
| Named neighbourhood | 450 | What the user sees |

- All cells share one `cell` table with a `cell_system` column, so another city can use hexagons throughout.
- A neighbourhood is a set of Output Areas in a reviewed CSV. Polygons are generated from it, never hand-drawn.
- Each destination hexagon gets a routing point moved onto the nearest walkable street inside it.
- The API serves only the neighbourhood-by-destination roll-up. Fine-grained matrices stay in object storage, so boundaries can change without re-routing.

## Consequences

- About 83 million origin-destination pairs per matrix instead of 279 million.
- Every boundary change is a reviewable diff.
- Travel times within a neighbourhood are summarised from LSOA centroids, so a large LSOA hides variation.

## What would change it

The phase 0b benchmark showing Output Area origins are affordable, or a second city with no small census units.
