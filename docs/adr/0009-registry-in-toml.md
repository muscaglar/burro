# 0009. The registry is TOML, one file per topic

Status: accepted, 2026-09-23

## Context

The plan first named the registry `sources.yaml`. The registry has a field, `commercial_use`, whose values include `yes` and `no`. Common YAML parsers read a bare `yes` or `no` as a boolean, so a hand-edited entry could silently change meaning. YAML also needs a third-party parser.

## Decision

The registry is a folder, `registry/sources/`, with one TOML file per dimension, read with the standard library's `tomllib`. Dates are native TOML dates.

It began as a single file. Once every source in the research was registered it held 110 entries and 270 KB, more than a person or an agent can sensibly read to add one source. A source must sit in the file named for its dimension, and the loader refuses it otherwise.

## Consequences

- One less dependency, and no ambiguity about `yes` and `no`.
- Arrays of tables are a little more verbose than YAML lists.
- Python's standard library cannot write TOML, so the registry is edited by hand or by a small script. That suits a file that should change rarely and be reviewed line by line.

## What would change it

A single dimension growing past what is comfortable to review. Then split that file, still in TOML.
