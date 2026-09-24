# 0004. OpenStreetMap for basemap and routing only

Status: accepted, 2026-09-23. Not reviewed by a lawyer.

## Context

OpenStreetMap is licensed under ODbL. A map drawn from it needs attribution only. A database derived from it, if used publicly, must be offered under ODbL too. The OpenStreetMap Foundation publishes no guideline on statistical aggregates, so whether per-area counts are a derived database is a grey area. Its Horizontal Layers guideline does say that adding other data on the basis of a comparison with OSM data triggers share-alike.

Burro's gazetteer and scores are its core assets. Every name and feature it needs is available under attribution-only licences.

## Decision

- OSM is used for the basemap and for the street network that routing runs over. Nothing else.
- OSM never enters the gazetteer or the scoring tables. The registry enforces this: a share-alike source cannot be registered for `gazetteer`, `cells`, `destination_search` or `scoring`, and the gate refuses a registry that breaks a rule.
- Walk-distance features use OS Open Roads, not the OSM network.
- OSM may be used to benchmark other data in aggregate. It may set a global threshold. It may never add, drop or correct an individual record.
- The routing network is built from OSM alone. Timetables are kept as a separate input.
- A public methods page names the OSM extract date, the routing engine version and its settings.
- OpenStreetMap is credited on the map and beside commute times, on web and iOS.

## Consequences

- The travel-time table is derived from OSM whatever we do. Keeping it on the server does not avoid the licence. The worst case is being asked to publish that table under ODbL, which we accept.
- Some features would be richer with OSM. They wait.

## What would change it

A Foundation guideline on aggregates, or a decision to publish OSM-derived feature tables openly. Any OSM-derived feature added later gets its own table and a published method.
