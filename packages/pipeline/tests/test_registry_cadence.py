"""How often a publisher says a dataset changes, as the registry's own words are read.

The registry's `cadence` is a sentence a person wrote. It is read by its first words
alone, into one of five rhythms, and what cannot be read so is not said. Every entry of
this repository is read here too, so that a word the reader does not know is found the
day it is written.
"""

from pathlib import Path

import pytest
from burro_pipeline.registry import load
from burro_pipeline.registry.cadence import DAYS, Cadence, read

REPOSITORY = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    ("words", "rhythm"),
    [
        ("Weekly", Cadence.WEEKLY),
        ("Monthly. Latest month July 2026.", Cadence.MONTHLY),
        ("Monthly, on the 20th working day.", Cadence.MONTHLY),
        ("Monthly releases. Latest seen 2026-08-19.0.", Cadence.MONTHLY),
        ("Quarterly: February, May, August, November.", Cadence.QUARTERLY),
        ("Annual. Latest year is 2024.", Cadence.YEARLY),
        ("Yearly", Cadence.YEARLY),
        ("One-off. Census Day was 21 March 2021.", Cadence.RARELY),
        ("One off. The page showed no update in a year.", Cadence.RARELY),
        ("Irregular. The edition before was of 2019.", Cadence.RARELY),
        ("Occasional. Version 2.3 published 13 February 2026.", Cadence.RARELY),
        ("Fixed to the 2021 Census.", Cadence.RARELY),
        ("Static per census.", Cadence.RARELY),
        ("Reissued when it is put right: this is V2.", Cadence.RARELY),
        ("Frozen. It was quarterly, and the edition of July was not published.", Cadence.RARELY),
    ],
)
def test_a_cadence_is_read_by_its_first_words(words: str, rhythm: Cadence):
    assert read(words) is rhythm


@pytest.mark.parametrize(
    "words",
    ["Daily", "Daily.", "Nightly refresh at about 02:00.", "Continuous. Refreshed as it is."],
)
def test_a_publisher_that_says_daily_is_read_as_weekly(words: str):
    """A week is the shortest rhythm that is counted in: no build is made each day."""
    assert read(words) is Cadence.WEEKLY


@pytest.mark.parametrize(
    ("words", "rhythm"),
    [
        ("Six-monthly, April and October", Cadence.QUARTERLY),
        ("Every six months, April and October.", Cadence.QUARTERLY),
        ("Twice a year, spring and autumn.", Cadence.QUARTERLY),
        ("About twice a year. Next release March 2027.", Cadence.QUARTERLY),
        ("About every two years. Next release to be announced.", Cadence.YEARLY),
    ],
)
def test_a_rhythm_between_two_is_read_as_the_shorter(words: str, rhythm: Cadence):
    """So that a file is called due too soon, and never too late."""
    assert read(words) is rhythm


@pytest.mark.parametrize(
    "words",
    [
        "",
        "   ",
        "The publisher states no update frequency for the files.",
        "The open data page says weekly. The forum says otherwise.",
        "Was quarterly on a rolling 12 months.",
        "None. The page says it was last updated over nine years ago.",
        # A word that only begins as a rhythm does is no rhythm.
        "Dailyish",
        "Monthlies are kept",
    ],
)
def test_what_cannot_be_read_by_its_first_words_is_not_said(words: str):
    assert read(words) is Cadence.NOT_SAID


def test_a_rhythm_that_has_a_length_has_the_longest_it_can_be():
    """A month is never over 31 days, a quarter never over 92 and a year never over 366. So
    a file is not called due before its publisher's rhythm has run once."""
    assert DAYS == {
        Cadence.WEEKLY: 7,
        Cadence.MONTHLY: 31,
        Cadence.QUARTERLY: 92,
        Cadence.YEARLY: 366,
    }
    assert Cadence.RARELY not in DAYS and Cadence.NOT_SAID not in DAYS


# The one entry that holds a receipt and whose publisher states no rhythm. Its cadence
# says so in words, and is read as not said until a person has found one.
STATES_NONE = {"tfl-step-free-station-topology"}


def test_every_entry_that_holds_a_receipt_says_a_cadence_that_is_read():
    registry = load(REPOSITORY / "registry" / "sources", enforce=False)
    held = {path.name for path in (REPOSITORY / "data" / "receipts").iterdir() if path.is_dir()}
    unread = {
        source.id
        for source in registry
        if source.id in held and read(source.cadence) is Cadence.NOT_SAID
    }
    assert unread == STATES_NONE
