"""How often a publisher says a dataset changes, read from the registry's own words.

An entry of the registry says under `cadence` how often its publisher updates the
dataset, in a sentence a person wrote. The step `fresh` counts in five rhythms, so the
sentence is read into one of them, by its first words alone: `Monthly, on the 20th
working day` is monthly, whatever follows. A sentence that does not begin with a word of
the table below is not read, and the rhythm is not said. Nothing is guessed from the
middle of a sentence: an entry that says `Was quarterly` is one a person must put right.

Two readings are choices, and each errs the same way, towards looking too soon:

- A publisher that says daily is read as weekly. A week is the shortest rhythm that is
  counted in, because no build is made each day.
- A rhythm that lies between two of the five is read as the shorter. Twice a year is
  read as quarterly, and every two years as yearly.

To teach the reader a word, add it to `WORDS` with a case in
`tests/test_registry_cadence.py`. To make an entry readable, begin its `cadence` with a
word of the table, and leave what the entry says after it as it is.
"""

import re
from enum import StrEnum


class Cadence(StrEnum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    # One off, fixed to a census, or put out when the publisher has something. It has no
    # length, so a file of it is never due by its age.
    RARELY = "rarely"
    # The entry says nothing, or nothing that is read.
    NOT_SAID = "not_said"


# How long each rhythm is at its longest, in days. A rhythm that is not here has no length.
DAYS = {Cadence.WEEKLY: 7, Cadence.MONTHLY: 31, Cadence.QUARTERLY: 92, Cadence.YEARLY: 366}

# The words a cadence may begin with, in small letters and with a space for a hyphen.
WORDS = {
    Cadence.WEEKLY: ("daily", "nightly", "weekly", "continuous"),
    Cadence.MONTHLY: ("monthly",),
    Cadence.QUARTERLY: ("quarterly", "six monthly", "every six months", "twice a year"),
    Cadence.YEARLY: ("annual", "annually", "yearly", "every two years"),
    Cadence.RARELY: (
        "one off",
        "irregular",
        "occasional",
        "fixed",
        "static",
        "reissued",
        "frozen",
    ),
}
# A word that says the rhythm is not exact, which may stand before it.
ABOUT = "about "
_BEGINS = {
    rhythm: re.compile(rf"(?:{'|'.join(re.escape(word) for word in words)})(?![a-z])")
    for rhythm, words in WORDS.items()
}


def read(words: str) -> Cadence:
    """The rhythm a cadence says, by its first words. Not said where they are not read."""
    plain = " ".join(words.lower().replace("-", " ").split()).removeprefix(ABOUT)
    for rhythm, begins in _BEGINS.items():
        if begins.match(plain):
            return rhythm
    return Cadence.NOT_SAID
