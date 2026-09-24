# 0001. Record decisions here

Status: accepted, 2026-09-23

## Context

Most of the code will be written by agents that start each session with no memory of the last. People forget too. A decision without its reason gets reversed by the next person who finds it inconvenient.

## Decision

Any decision that is expensive to reverse, or whose reason is not obvious from the code, gets a file in this folder. Each file has four parts: context, decision, consequences, and what would change it. Keep it under a page.

A change that contradicts a record updates the record in the same commit.

## Consequences

A little writing for every significant choice. In exchange, `AGENTS.md` stays short because it can point here.

## What would change it

Nothing foreseeable.
