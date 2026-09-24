"""The closed vocabulary of the rule-based reader, written down in one place.

The reader reads a sentence only when it knows every token in it. What it
knows is: a phrase of the lexicon, a name of the release, a number, and the
words of this file. Every other token makes the sentence unknown, and an
unknown sentence makes no edit.

So this file is the whole of what the reader may read through, and adding a
word to it is the only way to widen what it reads. It is reviewed as a whole.
A word belongs in `PLAIN` only if it can never turn a wish round, weaken it,
compare it, question it or give it to someone else, in any sentence that is
otherwise made of words from this file. If a word can do any of those it is
either left out, or it is one of the words below `PLAIN` that the reader has
an explicit rule for.

What is left out on purpose, so that nobody adds it without a rule:

- every past tense ("wanted", "loved", "was", "were", "did", "used"): the wish may be over;
- every third person ("wants", "needs", "works", "he", "she", "they", "people", "everyone",
  "you"): the wish may be someone else's;
- every word that asks ("who", "what", "why", "how", "should", "could", "do", "does");
- every word that weakens ("maybe", "perhaps", "quite", "fairly", "ideally", "if", "unless");
- every word that compares ("than" outside a limit, "rather", "instead", "prefer", "enough");
- every word of distance or absence ("far", "away", "miles", "off", "out", "none", "never").
"""

from typing import NamedTuple


class Words(NamedTuple):
    """Some words of the vocabulary, and why each of them is safe to read through."""

    why: str
    words: frozenset[str]


def _words(why: str, *words: str) -> Words:
    return Words(why, frozenset(words))


# A word typed with its apostrophe keeps it, written as "'", so that "we're" is never the
# past tense "were", nor "we'll" the adverb "well". The common way of leaving it out is
# listed only where the word it leaves is no other word.
PLAIN: tuple[Words, ...] = (
    _words(
        "The speaker, and nobody else. A wish is read only as the speaker's own.",
        *("i", "we", "i'm", "im", "i'd", "we're", "we'd", "me", "us", "my", "our"),
    ),
    _words(
        "To wish, in the present tense and the first person. Each says a thing is wanted "
        "and none says how much or whether. 'Like' also compares and 'love' is also a thing "
        "one has, so the reader reads those two only straight after the speaker.",
        *("want", "need", "like", "love", "would", "looking", "am", "must", "able", "after"),
    ),
    _words(
        "What Burro is asked to do. Each asks for a thing and says nothing of it.",
        *("find", "show", "give"),
    ),
    _words(
        "To be and to have, in the present tense. They join a thing to what is said of it.",
        *("is", "are", "be", "being", "has", "have", "it", "it's", "that", "that's", "there"),
        "there's",
    ),
    _words(
        "Articles and words of plenty. None says few, none or too many.",
        *("a", "an", "the", "some", "any", "lots", "lot", "of", "plenty", "loads", "many"),
    ),
    _words(
        "What a place to live is called. They name nothing that can be weighed.",
        *("somewhere", "place", "places", "area", "areas", "neighbourhood", "neighborhood"),
        *("location", "street", "streets", "home", "homes", "house", "houses", "buildings"),
        *("flats", "apartments", "part", "thing", "things", "something"),
    ),
    _words(
        "Words of good opinion. Each can only say that a thing is wanted.",
        *("good", "great", "nice", "lovely", "decent", "excellent", "best", "proper"),
        *("big", "large", "local", "handy", "quick"),
    ),
    _words(
        "Words that strengthen. 'Quite', 'fairly' and 'pretty' weaken, and are not here.",
        *("really", "very", "so", "definitely", "absolutely"),
    ),
    _words(
        "Where a thing is, and what joins one word to the next. 'Far', 'away', 'off', "
        "'out', 'over' and 'than' are not here, and nor is 'close' by itself, which is "
        "also what a pub does at night.",
        *("to", "in", "at", "by", "on", "for", "from", "with", "near", "nearby"),
        *("around", "within", "closer", "nearer"),
    ),
    _words(
        "What joins two wishes. 'But' begins a new wish and turns nothing by itself: "
        "'anything but' needs 'anything', which is not here.",
        *("and", "or", "but", "plus", "also"),
    ),
    _words(
        "How a place is reached, and how long it takes.",
        *("walk", "walks", "walking", "doorstep", "corner", "access", "live", "living"),
        *("minutes", "minute", "mins", "min"),
    ),
    _words(
        "Courtesy. It says nothing of the wish.",
        *("please", "thanks", "hi", "hello", "hey"),
    ),
    _words(
        "What is said of how much a thing counts, where it counts for more.",
        *("important", "matters", "matter", "priority", "weight", "emphasis"),
    ),
)
PLAIN_WORDS: frozenset[str] = frozenset(word for group in PLAIN for word in group.words)

_HOUSEHOLD = ("kids", "children", "family", "dog")
# Several words that are known together and not apart. "Foot" alone is no word of
# the reader's, and neither is "distance", "short", "easy", "well" or "thank".
PLAIN_PHRASES: frozenset[str] = frozenset(
    {
        "on foot",
        "walking distance",
        "short walk",
        "easy access",
        "as well",
        "thank you",
        "next to",
        "next door",
        "to me",
        "to us",
        "care about",
        "a bit of",
        "get to",
        "close by",
        "family home",
        "family house",
        # "Can" is known after the speaker and nowhere else: "can the pubs" scraps them.
        "i can",
        "we can",
        # Who a thing is for. It is known after "for" and "with" and nowhere else, so
        # that nobody but the speaker is ever the one who wishes: "kids love pubs".
        *(f"for {whose} {who}" for whose in ("the", "my", "our") for who in _HOUSEHOLD),
        *(f"with {who}" for who in ("kids", "children", "a dog", "a family")),
    }
)

# --- The words the reader has an explicit rule for ----------------------------
#
# None of these is read through. Each is either accounted for by the one rule
# that reads it, or the sentence it stands in makes no edit.

# The thing that follows is wanted not at all.
TURNS_FIRMLY: frozenset[str] = frozenset(
    {
        "no",
        "not",
        "without",
        "avoid",
        "avoiding",
        "don't want",
        "dont want",
        "do not want",
        "don't like",
        "dont like",
        "do not like",
        "not near",
        "not close to",
    }
)
# The thing that follows is wanted less.
TURNS_SOFTLY: frozenset[str] = frozenset(
    {
        "less",
        "fewer",
        "low",
        "lower",
        "not too",
        "not too many",
        "not too much",
        "not many",
        "not much",
        "not so",
        "not very",
        "not a lot of",
        "not lots of",
    }
)
# Said of how much a thing counts, and not of the thing: the weight is taken off.
TAKES_OFF: frozenset[str] = frozenset(
    {
        "don't care about",
        "dont care about",
        "do not care about",
        "don't need",
        "dont need",
        "do not need",
        "don't mind",
        "dont mind",
        "do not mind",
        "not bothered about",
        "not bothered by",
        "not bothered with",
        "not fussed about",
        "not fussed by",
        "ignore",
        "remove",
        "take off",
        "get rid of",
        "forget about",
    }
)
# The same, said after the thing: "parks are not important".
TAKES_OFF_AFTER: frozenset[str] = frozenset(
    {
        "not important",
        "don't matter",
        "dont matter",
        "do not matter",
        "doesn't matter",
        "doesnt matter",
        "does not matter",
    }
)
# The weight is turned down: before the thing, and after it.
TURNS_DOWN: frozenset[str] = frozenset(
    {"care less about", "less weight on", "less emphasis on", "lower priority on"}
)
TURNS_DOWN_AFTER: frozenset[str] = frozenset(
    {
        "less important",
        "not essential",
        "not a priority",
        "matters less",
        "matter less",
        "not as important",
        "not so important",
        "low priority",
        "lower priority",
    }
)
# What troubles a person. It is read of a nuisance alone, where it is the wish itself.
TROUBLES: frozenset[str] = frozenset(
    {"worry about", "worried about", "concerned about", "worries about"}
)
# The most a number may be. A number that is a minimum is never one of these: "at
# least", "more than", "no less than", "further than", "over" and "minimum" are no
# words of the reader's at all.
CAPS: frozenset[str] = frozenset(
    {"up to", "under", "within", "below", "max", "maximum", "less than", "around", "about"}
)
# The same, said so that the number is a limit and not a wish.
CAPS_FIRMLY: frozenset[str] = frozenset(
    {
        "no more than",
        "not more than",
        "at most",
        "at the most",
        "absolute max",
        "absolute maximum",
        "cannot go over",
        "can't go over",
        "cant go over",
    }
)
# A little more of a thing, and a lot.
SMALL_STEP: frozenset[str] = frozenset(
    {"more", "a bit", "bit", "a bit more", "slightly", "somewhat", "slightly more"}
)
LARGE_STEP: frozenset[str] = frozenset(
    {"much", "much more", "a lot", "a lot more", "lots more", "way more", "really", "very"}
)
# The thing is to count for as much as anything can.
ESSENTIAL: frozenset[str] = frozenset(
    {
        "essential",
        "must have",
        "must haves",
        "a must",
        "most important",
        "crucial",
        "vital",
        "top priority",
    }
)
# The area rules the contract defines, and "not far from", which is "near".
ONLY_IN: frozenset[str] = frozenset(
    {"only", "only in", "must be in", "has to be in", "have to be in"}
)
NOT_IN: frozenset[str] = frozenset({"not", "not in", "avoid", "avoiding", "anywhere but"})
NEAR_TO: frozenset[str] = frozenset(
    {"near", "near to", "close to", "next to", "not far from", "not too far from"}
)
# Known words that mean the opposite together. Each is held here so that it is one
# phrase the reader has no rule for, and the sentence it stands in is left unread.
NEVER_READ: frozenset[str] = frozenset({"a bit much", "so so", "bit much"})
# "A park too" is "a park as well". It is known there and nowhere else: "too many"
# and "too noisy" are no words of the reader's.
ALSO_AT_THE_END = "too"

# --- The written list of doubt --------------------------------------------------
#
# The reader does not read this list: none of these is a word it knows, so each
# makes a sentence unknown as any other word does. It is written down for two
# callers. The test of the vocabulary holds `PLAIN` to it, so that no word that
# ever turned a wish round is read through. And the model-backed reader, which
# may keep an edit drawn from a sentence the rules could not read, keeps none
# from a sentence that holds one of these (contract, section 8.2).
_TAKES_NT = (
    "is are was were do does did has have had ca could wo would should sha might must need "
    "ai dare ought may"
)
CONTRACTIONS: frozenset[str] = frozenset(
    spelling for stem in _TAKES_NT.split() for spelling in (f"{stem}n't", f"{stem}nt")
)
_DOUBT = (
    # What turns a wish round.
    "non none nope nah naw nae never neva nvr neither nor nothing nowt nowhere nobody "
    "wout sans zero nil cannot dnt un de anti nein nicht kein keine "
    "hardly barely rarely scarcely seldom "
    # What is wanted less.
    "lesser few least little minimal minimum moderation limited reduce reduced "
    "reducing than bottom lowest "
    "except excepting excluding exclude unless unlike regardless irrespective "
    "avoids avoided hate hates hated hating dislike dislikes disliked disliking "
    "loathe loathes detest detests despise despises skip ditch drop scrap rid stop stopped "
    "cease quit ban banned "
    # What is kept at a distance.
    "far further farther furthest farthest away miles distance distant outside beyond "
    # What qualifies a wish.
    "too enough against minus lack lacks lacking absence absent devoid free opposite wrong "
    # What a person is not sure of.
    "doubt doubts doubtful unsure unlikely unconvinced sceptical skeptical maybe perhaps "
    # What troubles a person.
    "worry worries worried worrying concern concerns concerned fear fears scared afraid "
    "nervous anxious "
    # What a person thinks little of.
    "bad awful terrible horrible dreadful worst rubbish overrated pointless useless boring "
    "annoying nightmare allergic bored meh suck sucks unimportant unnecessary unwanted "
    "unneeded uninterested disinterested indifferent unbothered unfussed irrelevant optional "
    # What is over, or is someone else's.
    "was were did had used once formerly wanted liked loved needed "
    "he she they you people everyone everybody anyone anybody someone others "
    # What asks.
    "who what why how should could"
)
# Several words that are doubt together: "anything but leafy", "the last thing I want".
PHRASES_OF_DOUBT: frozenset[str] = frozenset(
    {
        "last thing",
        "anything but",
        "anywhere but",
        "nothing but",
        "all but",
        "rather than",
        "instead of",
        "not for me",
        "cant stand",
        "a long way",
        "put off",
        "off putting",
        "sick of",
        "tired of",
        "fed up",
        "steer clear",
        "stay clear",
        "keep clear",
        "used to",
        "gone off",
        "went off",
        "give up",
        "giving up",
        "given up",
        "gave up",
        "done with",
        "pass on",
        "had it with",
        "last resort",
        "at a push",
        "if i must",
        "if i have to",
        "thumbs down",
        "dead body",
        "fat chance",
        "yeah right",
        "as if",
        "other than",
        "apart from",
        "aside from",
        "no longer",
        "any more",
        "at least",
        "more than",
        "no less than",
        "w o",
        "w out",
    }
)
WORDS_OF_DOUBT: frozenset[str] = frozenset(_DOUBT.split()) | CONTRACTIONS
