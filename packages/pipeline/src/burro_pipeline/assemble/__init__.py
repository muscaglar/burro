"""Assemble: put the geography and the measures of a build together as one release.

It reads no publisher's file itself. It takes what `cells` and `derive` worked
out, and makes of it a release that core will open, with the evidence behind
every figure and behind every figure that is missing.

| Module | Gives |
|---|---|
| `release.py` | The release and its evidence, from the spine, the outlines and the measures |
| `cli.py` | The step `preview`: one command from the store to a release a person can open |

What a first build has not measured is not in its release, and nothing stands
in for it. Such a release says it is a preview (ADR 0017).
"""
