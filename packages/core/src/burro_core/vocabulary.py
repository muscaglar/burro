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
# The same, said so that the number is a limit and not a wish. "At the very most" is "at
# most" said with more force: it was no word of the reader's, so a prompt that held it was
# not plain and its number was offered as a guide, which is less than the words say.
CAPS_FIRMLY: frozenset[str] = frozenset(
    {
        "no more than",
        "not more than",
        "at most",
        "at the most",
        "at the very most",
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
# What says, straight after a number of minutes, that it is the most a journey may take:
# "40 minutes max", "40 minutes or less". The reader reads none of these by this list: the
# grammar holds the words it places after a number. It is written down for whoever reads a
# time beside a place that is noticed, in a prompt that is not plain, and for whoever asks
# what puts a number in doubt: what caps a number is no doubt about it. Which of them make
# the number a limit is `FIRM_OF_MINUTES`, and no other list.
THE_MOST_AFTER: frozenset[str] = CAPS_FIRMLY | {
    *("max", "maximum", "tops", "or less", "or under"),
}
# What may be said of a time, straight after it, that leaves its number as it is: how exact
# it is, and that it is of the whole of the journey one way. "There and back" is twice the
# journey and "and a bit" is more than was read, so neither is here: after either the
# reader says that it could not take the time. It is for the same reader, and no word of it
# is a word of the grammar.
LEAVES_A_TIME_AS_IT_IS: frozenset[str] = frozenset(
    {
        *("or so", "or thereabouts", "ish", "exactly", "roughly", "approximately"),
        *("each way", "one way", "door to door", "in all", "in total", "all in", "all told"),
        "total",
    }
)
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
# What a person cannot bear, or asks to be kept from. A sentence that holds one and names
# nothing may head a list of things that are not wanted, with no colon to say so: "Things
# I hate", "What I want to avoid". A word that turns and says no more of what, "not",
# "no", is not among them: "Not sure where to begin" heads nothing.
CANNOT_BEAR: frozenset[str] = frozenset(_CANNOT_BEAR.split()) | frozenset(
    {"cant stand", "avoid", "avoiding", "dont want", "do not want", "dont like", "do not like"}
)
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
# What leads in to a clause and says which case it is said of: "if I'm buying, max £400k".
# It is no word of the grammar, so a prompt that holds it is not plain and nothing of it is
# applied. It is no doubt about the home either: whoever says which of renting and buying
# they mean has said it, and the clause is read as it would be without the word. Where it
# sets one case against another, "if I rent ..., if I buy ...", the words name both tenures,
# and which is meant is the person's to say. Decided on 2026-09-25.
IN_CASE: frozenset[str] = frozenset({"if"})
# --- What asks for nothing ---------------------------------------------------------
#
# The reader says where the words stand that it made nothing of, so that a person sees
# what was missed. In a prompt that is not plain most of them are how a wish is said,
# and no wish: "I want to live somewhere", "with access to", "but with some", "around
# it", "if I'm", "for". Said to be unread, they were taken for something Burro had
# missed. So a stretch that holds nothing but such words is not said to be unread.
#
# Each list is one the grammar holds already, and none holds a word that turns, takes
# off, caps, compares, weakens or says how much. No meaning is guessed at: a word that
# is on none of them is unread wherever nothing was made of it, and so is the whole of
# every stretch that holds one. A word that wishes is not among them by itself. It asks
# for nothing only where the grammar places it, straight after the speaker, "I want":
# anywhere else it may compare, or be another's, "pubs like I need noise", "some want
# pubs". `grammar.py` adds the words that stand between the parts of a home.
LEADS_IN: tuple[Words, ...] = (
    SPEAKER,
    ASKS_BURRO,
    TO_DO,
    SOMEWHERE,
    SOMEWHERE_THAT,
    ARTICLE,
    WHOSE,
    NEARBY,
    JOINS,
    COURTESY,
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
# What carries a turn on, and is no second turn beside the word it follows: "neither parks
# nor pubs" turns both away once, and "further than" is one word for far. It is for whoever
# counts the words that turn before a thing: two may turn a wish round twice, which is to
# wish for the thing, "I can't live without a park", and these two never do.
CARRIES_A_TURN: frozenset[str] = frozenset({"nor", "than"})
# What holds a word that turns, and turns nothing: "a few restaurants" and "a little
# centre" say some of a thing, and "nothing but parks" says that nothing else will do. It is
# for whoever counts the words that turn before a thing. The reader reads none of them:
# "few", "little" and "nothing" are no words of the grammar, so a prompt that holds one is
# not plain, as it was, and nothing of it is applied.
TURNS_NOTHING: frozenset[str] = frozenset({"a few", "quite a few", "a little", "nothing but"})
# What turns a wish only where it is the whole of what stands between two marks: "pubs,
# pass". Among other words it says something else, "a park I pass on my way to work", so it
# is no word of doubt and no word of dread. "Pass on" is a phrase of doubt wherever it
# stands. It is for whoever asks what the words beyond a mark say of a thing.
TURNS_WHERE_IT_STANDS_ALONE: frozenset[str] = frozenset({"pass", "hard pass"})

# --- Where what is said next begins -------------------------------------------------------
#
# The reader reads none of these by these lists: each is a word it knows already, or one it
# does not know at all. They are written down for whoever asks what a word that turns is
# said of, in a sentence that is no plain list. Such a word leads up to the thing it is
# said of, and no further. It was held to lead up to every thing after it until a mark, so
# of "I'm tired of the city and want somewhere leafy" the wish was read as turned away, and
# a person was told that they did not want what they had asked for.
#
# What leads in a wish of the speaker's own whose speaker is left unsaid: "and want", "so
# need", "but love". "Or" is not among them. After a word that turns it carries the turn, so
# "I don't want pubs or need a station" asks for neither.
LEADS_IN_A_WISH: frozenset[str] = frozenset({"and", "but", "so", "plus", "also"})
# What leads in words that the speaker opens, or that a turn of their own opens: "and I
# never", "or no", "so we". "With" joins a thing to the thing before it, and what is said
# before it may be said of both: "I don't want a park with no pubs".
LEADS_IN_WHAT_IS_SAID_NEXT: frozenset[str] = LEADS_IN_A_WISH | {"or"}
# What begins a reason, wherever it stands. What follows it is said of what the reason
# names, and what stands before it of what was wished: "somewhere quiet because I hate the
# city". "As" and "since" are as often said of a time or of a likeness, so neither is here.
GIVES_A_REASON: frozenset[str] = frozenset({"because"})

# --- A place that is no place to reach -------------------------------------------------
#
# The reader reads none of these either. In a prompt that is not plain, a place that is
# named is offered as a journey to it, and one press may take a journey. So what says
# that a place is to be kept away from, or is somebody else's, is written down here, for
# whoever offers a journey. Decided on 2026-09-25: a person who asks to live far from
# somebody is never ranked by how near they are to them.

# What keeps a place at a distance, wherever it stands in the sentence of the place: "far
# from", "well away from", "as far as possible from", "nowhere near". Every one is a word
# or a phrase that is listed above as one that turns a wish away or puts it in doubt.
STAYS_AWAY: frozenset[str] = frozenset(
    {
        *("far", "further", "farther", "furthest", "farthest", "away"),
        *("not near", "not close to", "nowhere near", "avoid", "avoiding", "anywhere but"),
        *("a long way", "steer clear", "stay clear", "keep clear"),
    }
)
# What says near with a word for far, and is no wish to stay away: "not far from".
NOT_FAR: frozenset[str] = frozenset(
    {"not far", "not too far", "not that far", "not so far", "not very far"}
)
# What turns a word for far or for a least round, wherever it stands before it in its
# clause, so that the words say near or say the most: "neither of us is more than 40
# minutes", "I don't want to move far", "it's impossible for me to be far from".
TURNS_ROUND: frozenset[str] = (
    frozenset({"no", "not", "never", "cannot", "neither", "nor", "impossible", "unable"})
    | CONTRACTIONS
)
# What says a number is the least it may be, straight before the number or straight after
# what it is a number of: "at least 30 minutes", "30 minutes or more". A number that is a
# least is never read as the most. "Over" is one only against a number.
AT_LEAST: frozenset[str] = frozenset(
    {
        *("at least", "at the least", "no less than", "not less than", "more than"),
        *("over", "minimum", "a minimum of", "minimum of", "or more", "upwards of"),
    }
)
# Whose place it is, where the words name somebody who is not the speaker: "my ex lives
# at", "his mother is in". `WHO_ELSE` is said of a wish. Of a place it is said with whose
# it is in the third person too.
SOMEBODY_ELSE: frozenset[str] = WHO_ELSE | frozenset(
    {"his", "her", "their", "he's", "she's", "they're"}
)
# Who shares the speaker's home, so that where they work or learn is a place the household
# must reach: "my partner works at", "and my partner at".
OF_THE_HOUSEHOLD: frozenset[str] = frozenset(
    f"{whose} {who}"
    for whose in ("my", "our")
    for who in (
        *("partner", "wife", "husband", "girlfriend", "boyfriend", "fiance", "fiancee"),
        *("kid", "kids", "child", "children", "son", "sons", "daughter", "daughters"),
    )
)
# What says where somebody lives, which is no place that they go to: "my partner lives
# at". Of one of the household it is no place the words say must be reached.
LIVES_THERE: frozenset[str] = frozenset(
    {"lives", "live", "living", "stays", "stay", "staying", "resides", "is from", "are from"}
)
# A place that was left: "we moved from".
LEFT_BEHIND: frozenset[str] = frozenset({"moved from", "moving from", "move from"})
WORDS_OF_DOUBT: frozenset[str] = (
    frozenset((_DOUBT + " " + _DREADED + _AT_LARGE).split()) | WORDS_THAT_TURN_AWAY
)

# --- What is said of one's own words, and of no wish ----------------------------------
#
# What a person says of their own words: that they mean them, that it is what they think,
# that it is how they would have it. The reader reads none of these, and none is a word of
# the grammar: a prompt that holds one is not plain, and nothing of it is applied. The
# reader holds one to ask for nothing where it is the whole of a part of its sentence, so
# that it is not said to be unread, and makes nothing else of it. They are
# written down for whoever marks which way the words give of a thing that was noticed. Set
# apart by a mark, in a part of its sentence that holds nothing else, one of these says
# nothing of which way a thing is wanted, so the rest of the sentence gives the way it would
# give without it: "honestly, somewhere calm" is Going out towards Calm, as "somewhere
# calm" is. Anywhere else in a sentence it is a word the reader does not know.
#
# The list is closed, and is held to what it may never hold: a word that turns, takes off,
# compares or asks, a past tense, and anybody but the speaker. "Maybe", "perhaps" and
# "probably" are not here. Each may stand for a wish that is not: "a station, maybe not".
ASIDES: frozenset[str] = frozenset(
    {
        # That the words are meant.
        *("honestly", "to be honest", "frankly", "truthfully", "really", "basically"),
        # That it is what the speaker thinks.
        *("i think", "i guess", "i suppose", "i reckon", "i feel", "personally"),
        # That it is how the speaker would have it.
        *("ideally", "if possible", "preferably", "hopefully"),
    }
)

# What heads a list of things that are wanted, before a colon: "Must haves: a park, a
# station". The reader reads none of these: a colon joins nothing, so a sentence that holds
# one is not plain. They are written down for whoever holds what is offered of a thing to
# the words it stands in. What stands before a colon is said of all that is listed after
# it, and as often says that none of it is wanted: "Dealbreakers: pubs, a station". No list
# of such words is ever whole, so it is the headings that say a thing is wanted that are
# listed, and a heading of any other words leaves what stands under it to the person.
HEADS_WHAT_IS_WANTED: frozenset[str] = frozenset(
    {
        *("wants", "needs", "likes", "musts", "must have", "must haves", "essentials"),
        *("priority", "priorities", "top priority", "top priorities", "requirements"),
        *("criteria", "preferences", "wish list", "wishlist", "pros", "nice to have"),
        *("nice to haves", "main thing", "main things", "key things", "ideally"),
        *("positives", "in order", "in order of importance"),
    }
)
# What opens a heading and says nothing of what it heads: "What I want:", "Things I care
# about:". It is a word that asks anywhere else, and a sign of doubt there. What follows
# it says whether the list is of what is wanted: "What I hate:" is held to "hate".
OPENS_A_HEADING: frozenset[str] = frozenset({"what", "things", "the things"})
# What a heading says of the words under it, and of no wish: how long they are. "Short
# version: quiet, leafy, near a station". Set apart by its colon, it says nothing of which
# way a thing is wanted, as what is said of one's own words says nothing.
SAYS_HOW_LONG: frozenset[str] = frozenset(
    {"short version", "long version", "the short version", "the long version", "in short"}
)

# --- An amount that is said by no month ------------------------------------------------
#
# The reader reads none of these either, and none is a word of the grammar: a prompt that
# holds one is not plain, and nothing of it is applied. A rent is held by the month, so an
# amount that is said by any other period is no amount the search can hold at the figure
# that was typed. They are written down for whoever offers an amount: "£350 a week" was
# offered as a budget of £350 a month. Since 2026-09-26 an amount by the week is offered
# as what it comes to by the month, and says that it was worked out and from what. An
# amount by any other period is not read, since no rule says what it comes to.
BY_THE_WEEK: frozenset[str] = frozenset(
    {"a week", "per week", "each week", "every week", "weekly", "pw", "a wk", "per wk"}
)
BY_ANOTHER_PERIOD: frozenset[str] = frozenset(
    {
        *("a day", "per day", "daily", "a night", "per night", "nightly"),
        *("a fortnight", "per fortnight", "fortnightly"),
        *("a quarter", "per quarter", "quarterly", "a term", "per term"),
        *("a year", "per year", "yearly", "annually", "per annum", "pa"),
    }
)
# Every word that names a period an amount may be paid by, but the month. The two lists
# above hold the ways of saying a period that the reader knows what to make of. No such
# list is ever complete: "£350 this week", "£350 per person per week", "£700 every two
# weeks", "£18,000 each year" and "annual rent of £18,000" were each offered as an amount
# by the month at the figure that was typed. So where one of these words stands beside an
# amount in any other way, the amount is by no month and is not read: nobody can say what
# it comes to. None is a word of the grammar, and the month itself is none of them: "a
# month", "monthly" and "pcm" say that an amount is by the month. Add a word for a period here.
OF_A_PERIOD: frozenset[str] = frozenset(
    {
        *("week", "weeks", "weekly", "wk", "wks", "wkly", "pw", "ppw", "pppw"),
        *("weekend", "weekends", "fortnight", "fortnights", "fortnightly"),
        *("biweekly", "bi-weekly"),
        *("day", "days", "daily", "night", "nights", "nightly"),
        *("quarter", "quarters", "quarterly", "term", "terms", "termly"),
        *("year", "years", "yearly", "yr", "yrs", "annual", "annually", "annum", "pa"),
        # More months than one, which is no month: "£9,000 for 6 months".
        *("months", "mths", "bimonthly", "bi-monthly"),
    }
)
