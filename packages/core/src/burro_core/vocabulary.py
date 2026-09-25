"""The words of the grammar of a plain prompt, written down in one place.

The rule-based reader applies a prompt only when the whole of it is a plain
list of things wanted or not wanted, with an optional opening, a budget and
a journey. `grammar.py` holds the grammar, and this file the words it is
made of. For any other prompt the reader applies nothing, and offers what it
noticed for the person to choose (ADR 0012).

A word here is known only where the grammar places it. "Want" is a wish
straight after the speaker and nothing anywhere else, so "some want pubs"
is not plain. That is why a word may be here that can turn a wish round in
another place: what makes a prompt plain is its shape, and not that each of
its words is on a list.

The grammar is wide for what is structured: a budget, a tenure, the size of
a home and a journey are made of numbers, names of the release and closed
lists of words, so a wrong reading is a wrong number and not a wish turned
round. It is narrow for a wish about character, which is read only from a
phrase of the lexicon. A new word for one is a case in `evals/` first.

What is left out on purpose, so that nobody adds it without a rule:

- every past tense ("wanted", "loved", "was", "were", "did", "used"): the wish may be over;
- every third person ("wants", "needs", "works", "he", "she", "they", "people", "everyone",
  "you"): the wish may be someone else's;
- every word that asks ("who", "what", "why", "how", "should", "could", "do", "does");
- every word that weakens the whole of a wish ("maybe", "perhaps", "ideally", "probably", "if",
  "unless"): it says whether a thing is wanted. A word of degree before a thing, "fairly",
  "quite", says how much, and is a small step;
- every word that compares ("than" outside a limit, "rather", "instead", "prefer", "enough");
- every word of distance or absence ("far", "away", "miles", "off", "out", "none", "never").
"""

from typing import NamedTuple


class Words(NamedTuple):
    """Some words of the grammar, where it places them, and why that is safe."""

    why: str
    words: frozenset[str]


def _words(why: str, *words: str) -> Words:
    return Words(why, frozenset(words))


# A word typed with its apostrophe keeps it, written as "'", so that "we're" is never the
# past tense "were", nor "we'll" the adverb "well". The common way of leaving it out is
# listed only where the word it leaves is no other word.
SPEAKER = _words(
    "The speaker, and nobody else, at the head of a wish. A wish is read only as the "
    "speaker's own.",
    *("i", "we", "i'm", "im", "i'd", "we're", "we'd"),
)
WISH = _words(
    "To wish, in the present tense, straight after the speaker. Each says a thing is wanted "
    "and none says how much or whether. 'Looking for' is a wish with no speaker too, as a "
    "search is typed.",
    *("want", "need", "like", "love", "after", "looking for", "looking to", "care about"),
    *("would like", "would love", "would want", "am after", "am looking for"),
    *("am looking to", "are after", "are looking for", "are looking to"),
)
WISH_ALONE = frozenset({"looking for", "looking to"})
ASKS_BURRO = _words(
    "What Burro is asked to do, at the head of a wish. It asks for a thing and says nothing of it.",
    *("find me", "find us", "show me", "show us", "give me", "give us"),
)
TO_DO = _words(
    "What the speaker wishes to do, after the wish: to live somewhere, or to have a thing.",
    *("to live", "to be", "to find", "to have", "to live in", "to be in", "being"),
)
SOMEWHERE = _words(
    "What a place to live is called, at the head of a wish. It names nothing that can be weighed.",
    *("somewhere", "something", "a place", "an area", "a neighbourhood", "a neighborhood"),
    "a location",
)
SOMEWHERE_THAT = _words(
    "What joins a place to what is wanted of it. 'With' does too, and is a word that joins.",
    *("that is", "that has", "that's"),
)
PLACE_NOUN = _words(
    "What a place, or what stands in it, is called, straight after a thing: 'a leafy area' "
    "is 'leafy', and 'Victorian terraces' is 'Victorian'.",
    *("area", "areas", "place", "places", "neighbourhood", "neighborhood", "location"),
    *("street", "streets", "part of town", "buildings", "terraces", "houses", "homes"),
    *("living", "walks", "vibe", "feel"),
)
ARTICLE = _words(
    "Articles and words of plenty, straight before a thing. None says few, none or too many.",
    *("a", "an", "the", "some", "any", "lots", "lot", "of", "plenty", "loads", "many"),
)
GOOD = _words(
    "Words of good opinion, before a thing or after 'would be'. Each can only say that a "
    "thing is wanted.",
    *("good", "great", "nice", "lovely", "decent", "excellent", "best", "proper"),
    *("big", "large", "local", "handy", "quick"),
)
STRENGTHENS = _words(
    "Words that strengthen, before a wish or before what is said of a thing. 'Quite', "
    "'fairly' and 'pretty' say a little, and are words of degree.",
    *("really", "very", "so", "definitely", "absolutely"),
)
IMPORTANT = _words(
    "What is said of how much a thing counts, after the thing, where it counts for more.",
    *("important", "a priority", "matters", "matter"),
)
WHOSE = _words(
    "To whom a thing counts, after what is said of it. The speaker alone.",
    *("to me", "to us", "for me", "for us"),
)
NEARBY = _words(
    "Where a thing is wanted, straight after it: near. 'Far', 'away' and 'off' are not here. "
    "'Around' stands here after a thing alone, where it is no word for about a number.",
    *("nearby", "close by", "on my doorstep", "on the doorstep", "round the corner"),
    *("around the corner", "within walking distance", "in walking distance"),
    *("i can walk to", "we can walk to", "i can get to on foot", "we can get to on foot"),
    *("around", "around it"),
)
FOR_WHOM = _words(
    "Whom a thing is for, after the thing: the speaker's own household, and nobody who "
    "lives somewhere.",
    *("for the kids", "for my kids", "for our kids", "for the dog", "for my dog"),
)
JOINS = _words(
    "What joins two wishes. 'But' begins a new wish and turns nothing by itself.",
    *("and", "or", "but", "plus", "also", "with"),
)
COURTESY = _words(
    "Courtesy, alone in a sentence or at its end. It says nothing of the wish.",
    *("please", "thanks", "thank you", "hi", "hello", "hey"),
)
# Every group of plain words, to be reviewed as a whole.
PLAIN: tuple[Words, ...] = (
    SPEAKER,
    WISH,
    ASKS_BURRO,
    TO_DO,
    SOMEWHERE,
    SOMEWHERE_THAT,
    PLACE_NOUN,
    ARTICLE,
    GOOD,
    STRENGTHENS,
    IMPORTANT,
    WHOSE,
    NEARBY,
    FOR_WHOM,
    JOINS,
    COURTESY,
)
PLAIN_WORDS: frozenset[str] = frozenset(word for group in PLAIN for word in group.words)

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
        "no further than",
    }
)
# What makes an amount of money a firm limit, and what makes a number of minutes one.
# Decided on 2026-09-24: "max" and "up to" say the most that can be paid, and "max" and
# "within" the longest a journey may be. Read as a guide, "max £400k" put first an area
# where a home sold for far more. With none of these words a number stays a guide, which
# lowers an area's fit and leaves none out. "Up to" makes no journey firm and "within" no
# budget: each is held to the list it was decided for.
FIRM_OF_MONEY: frozenset[str] = CAPS_FIRMLY | {"max", "up to"}
FIRM_OF_MINUTES: frozenset[str] = CAPS_FIRMLY | {"max", "within"}
# A thing is wanted, and not very much. Each stands before a thing, or inside
# the speaker's own wish, "I would quite like", where it says how much and
# never whether: none can turn a wish round. Under a word that turns, "not
# quite", the prompt is not plain, as with any word of degree. They made a
# prompt a question while "a bit" and "slightly" were read.
SOFTLY: frozenset[str] = frozenset({"fairly", "quite", "pretty", "reasonably", "relatively"})
# A little more of a thing, and a lot.
SMALL_STEP: frozenset[str] = SOFTLY | frozenset(
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
        "a must have",
        "must be",
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
    {
        "near",
        "near to",
        "close to",
        "next to",
        "not far from",
        "not too far from",
        "walking distance to",
        "walking distance of",
        "within walking distance of",
        "a short walk to",
        "a short walk from",
        "easy access to",
        # To have access to a thing is to be near it. Under a word that turns,
        # "no access to", it is no word of the grammar, as no word for near is.
        "access to",
        "closer to",
        "nearer to",
        "by",
        "able to walk to",
        "can walk to",
        "i can walk to",
        "we can walk to",
    }
)
# What may close a sentence after the last wish: courtesy, and "too", which is "as
# well" there and nowhere else. "Too many" and "too noisy" are no words of the grammar.
AT_THE_END: frozenset[str] = COURTESY.words | {"too", "as well"}

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
# What turns a wish away: the thing that follows is not wanted, or is wanted
# less, or is wanted at a distance. In a prompt that is not plain, a choice
# that has one direction is never offered for a thing that stands after one.
# What a person cannot bear. Before a thing it turns the wish away, as the words beside
# it do. After one it is said of the thing: "a playground by the house, I'd hate that".
_CANNOT_BEAR = (
    "hate hates hated hating dislike dislikes disliked disliking "
    "loathe loathes detest detests despise despises "
)
_AWAY = (
    # What turns a wish round.
    "non none nope nah naw nae never neva nvr neither nor nothing nowt nowhere nobody "
    "wout sans zero nil cannot dnt un de anti nein nicht kein keine "
    "hardly barely rarely scarcely seldom "
    # What is wanted less.
    "lesser few least little minimal minimum moderation limited reduce reduced "
    "reducing than bottom lowest "
    "except excepting excluding exclude unless unlike regardless irrespective "
    "avoids avoided " + _CANNOT_BEAR + "skip ditch drop scrap rid stop stopped "
    "cease quit ban banned "
    # What is kept at a distance.
    "far further farther furthest farthest away miles distance distant outside beyond "
)
# What a person dreads or thinks little of. Said of a thing, before it or after, it is
# no wish for the thing: "a pub on the corner would be hell", "a station, heaven forbid".
# Of a nuisance it is the wish itself: to dread noise is to want less of it.
_DREADED = (
    # What troubles a person.
    "worry worries worried worrying concern concerns concerned fear fears scared afraid "
    "nervous anxious "
    # What a person thinks little of.
    "bad awful terrible horrible dreadful worst rubbish overrated pointless useless boring "
    "annoying nightmare allergic bored meh suck sucks unimportant unnecessary unwanted "
    "unneeded uninterested disinterested indifferent unbothered unfussed irrelevant optional "
    # What a person dreads.
    "dread dreads dreaded dreading hell hellish ghastly grim horrid vile gross yuck ugh "
    "eww ew disaster misery miserable unbearable insufferable torture "
)
_DREADED_IN_A_PHRASE = frozenset({"heaven forbid", "god forbid", "god no", "perish the thought"})
DREADS: frozenset[str] = frozenset((_DREADED + _CANNOT_BEAR).split()) | _DREADED_IN_A_PHRASE
# Whose wish it is, where the words say it is not the speaker's. A thing that stands
# with one is offered, and which way it runs is for the person to say: "my mum is after
# a park" may be why a park is wanted, and may be nothing of the person's at all. The
# speaker's own household is not here: `FOR_WHOM` holds whom a thing may be wanted for.
# It is said of a wish and never of a journey: where a partner works is a place to reach.
# So who is known to the speaker and the third person of a wish are no signs of doubt.
_AT_LARGE = "he she they people everyone everybody anyone anybody someone others "
_KNOWN_TO_THE_SPEAKER = (
    "mum mom mam mother dad father parents partner wife husband girlfriend boyfriend "
    "brother sister friend friends mate mates flatmate housemate landlord boss ex"
)
WHO_ELSE: frozenset[str] = frozenset(_AT_LARGE.split()) | frozenset(
    f"my {who}" for who in _KNOWN_TO_THE_SPEAKER.split()
)
# The third person of each word of `WISH`. It says whose wish it is only where somebody
# stands straight before it: "Wants: a park" is the heading of a list.
WISHES_OF_ANOTHER: frozenset[str] = frozenset(
    {"wants", "needs", "likes", "loves", "prefers", "fancies", "cares about"}
    | {"is after", "is looking for", "is looking to", "is keen on"}
)
# What stands for a thing that was named, and says nothing of its own: "that", of "a
# station, I'd hate that".
STANDS_FOR: frozenset[str] = frozenset({"it", "that", "this", "them", "those", "these", "one"})
_DOUBT = (
    # What qualifies a wish.
    "too enough against minus lack lacks lacking absence absent devoid free opposite wrong "
    # What a person is not sure of.
    "doubt doubts doubtful unsure unlikely unconvinced sceptical skeptical maybe perhaps "
    # What is over.
    "was were did had used once formerly wanted liked loved needed "
    # Whom a thing is said of at large, who is as often anybody as somebody else.
    "you "
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
        "no more",
        "any more",
        "at least",
        "more than",
        "no less than",
        "w o",
        "w out",
    }
    | _DREADED_IN_A_PHRASE
)
WORDS_THAT_TURN_AWAY: frozenset[str] = frozenset(_AWAY.split()) | CONTRACTIONS
WORDS_OF_DOUBT: frozenset[str] = (
    frozenset((_DOUBT + " " + _DREADED + _AT_LARGE).split()) | WORDS_THAT_TURN_AWAY
)
