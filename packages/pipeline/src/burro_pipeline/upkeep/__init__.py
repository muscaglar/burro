"""Keeping a city up to date: what is held and how old it is, and what moved between two builds.

`fresh` reads the registry, the lists and the receipts, and says of every file that has a
receipt whether it is time to look at its publisher's page again. `moved` reads two
releases, each with its evidence, and says what differs, so that a person approves a
fresh build knowing what changed. Neither fetches, builds or changes anything.
"""
