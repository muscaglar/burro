import pytest
from burro_core.explain import TEMPLATES, render
from burro_core.facts import STANDINGS, Fact, facts_for
from burro_core.ids import Mode, Provenance, SentenceOrigin, Strictness, TemplateId, VerdictReason
from burro_core.spec import Commute, PreferenceSpec
from burro_core.verify import BANNED_WORDS, ORDINARY_WORDS, Sentence, verify

from .support import area_id, build_worked_release, build_worked_spec, place_id, small_release

AREA = area_id(1)
PARK = f"{AREA}/feature/park_proximity"
NOISE = f"{AREA}/feature/noise_exposure"
NAME = f"{AREA}/area/name"
RENT = f"{AREA}/cost/rent.bed_1"
JOURNEY = f"{AREA}/travel/syn-p0001.pt"
STATION = f"{AREA}/station/syn-s0001"


def spec() -> PreferenceSpec:
    worked = build_worked_spec()
    by_bike = Commute(
        place_id=place_id(3),
        mode=Mode.CYCLE,
        max_minutes=40,
        strictness=Strictness.SOFT,
        provenance=Provenance.STATED,
    )
    return worked.replace(commutes=(*worked.commutes, by_bike))


def facts(area: str = AREA) -> dict[str, Fact]:
    return {f.fact_id: f for f in facts_for(small_release(), area, spec())}


def said(text: str, *cited: str) -> Sentence:
    return Sentence(text=text, fact_ids=cited, origin=SentenceOrigin.MODEL)


def reason(text: str, *cited: str) -> VerdictReason:
    verdict = verify(said(text, *cited), facts())
    assert verdict.ok == (verdict.reason is VerdictReason.OK)
    return verdict.reason


def test_the_facts_these_tests_lean_on_are_what_they_say():
    found = facts()
    assert found[PARK].slots["value"] == "20 m"
    # Of the seven areas compared, four are further from a park and five are noisier.
    assert found[PARK].numbers == ("20", "57%", "7")
    assert found[NOISE].numbers == ("15%", "71%", "7")
    assert found[NAME].names == ("Alderwick", "Quillhaven")
    assert found[JOURNEY].numbers == ("15", "20")
    assert found[STATION].names == ("Pellam Cross", "Amber line", "Birch line")
    assert found[RENT].numbers == ("£1100", "£1250", "£1400", "2026", "08", "8")


@pytest.mark.parametrize(
    ("text", "cited"),
    [
        ("Alderwick is in Quillhaven.", (NAME,)),
        ("It is a 20 m walk to a park, closer than 57% of the 7 areas compared.", (PARK,)),
        ("Alderwick is quieter than 71% of the seven areas compared.", (NAME, NOISE)),
        ("Quieter than 71 per cent of areas in this release.", (NOISE,)),
        ("The nearest park of 2 ha or more is 20 m away.", (PARK,)),
        ("About 15 minutes to Pellam Cross by public transport.", (JOURNEY,)),
        ("Pellam Cross is about 4 minutes away on foot, on the Amber line.", (STATION,)),
        ("From Alderwick, Pellam Cross is 15 minutes away.", (NAME, JOURNEY)),
        ("A 1-bedroom home rents for £1,100 to £1,400 a month, as of August 2026.", (RENT,)),
        ("Rent runs from 1100 to 1400.0 pounds.", (RENT,)),
        ("In Alderwick the nearest park is 20 m away.", (NAME, PARK)),
        ("This area has a park nearby.", ()),
        ("It is closer to a park than most.", (PARK,)),
    ],
)
def test_a_supported_sentence_is_accepted(text: str, cited: tuple[str, ...]):
    assert reason(text, *cited) is VerdictReason.OK


@pytest.mark.parametrize(
    ("text", "cited"),
    [
        ("It is a 25 m walk to a park.", (PARK,)),
        ("Closer to a park than 80% of areas in this release.", (PARK,)),
        ("Quieter than 71.5% of areas.", (NOISE,)),
        # What the sentences said before: the percentile the area is scored on.
        ("Closer to a park than 64% of areas in this release.", (PARK,)),
        ("Quieter than 79% of areas in this release.", (NOISE,)),
        ("Rent for a 1-bedroom home is about £1,250.50 a month.", (RENT,)),
        # The number is true of the journey, and the sentence cites the park.
        ("About 15 minutes to a park.", (PARK,)),
        ("About 15 minutes away.", ()),
        ("It has been this way since 1987.", (NAME,)),
        ("Rents are around £1,400 to £14,000.", (RENT,)),
    ],
)
def test_an_invented_number_is_rejected(text: str, cited: tuple[str, ...]):
    assert reason(text, *cited) is VerdictReason.UNSUPPORTED_NUMBER


@pytest.mark.parametrize(
    ("text", "cited"),
    [
        ("Alderwick is close to Victoria Park.", (NAME, PARK)),
        ("Alderwick is in London.", (NAME,)),
        ("Quieter than 71% of London.", (NOISE,)),
        ("Alderwick has a lovely Waitrose.", (NAME,)),
        ("The Dog and Duck is nearby.", (NAME,)),
        # Both names are real, and neither fact that holds them is cited.
        ("Alderwick is in Quillhaven.", (PARK,)),
        ("Alderwick is in Quillhaven.", ()),
        # The two parts are allowed names. The whole is a place nobody recorded.
        ("Alderwick Cross is nearby.", (NAME, STATION)),
        ("Pellam Cross Road is nearby.", (STATION,)),
        ("The Alderwick Arms is nearby.", (NAME,)),
        ("Alderwick The Great is nearby.", (NAME,)),
        ("It is in the borough. The Quillhaven Tavern is there.", (NAME,)),
        ("Parks are close by.", (PARK,)),
        ("It is on the Jubilee line.", (STATION,)),
    ],
)
def test_an_invented_proper_noun_is_rejected(text: str, cited: tuple[str, ...]):
    assert reason(text, *cited) is VerdictReason.UNSUPPORTED_NAME


@pytest.mark.parametrize(
    "text",
    [
        "three parks are nearby.",
        "it has the second quietest streets.",
        "there are twenty parks.",
        "a hundred metres from a park.",
        "there are twenty-one parks.",
        "a thousand homes.",
        "it is about thirty minutes from the office.",
        "rents have fallen by forty percent.",
        "a million people visit each year.",
        "a billion pounds was spent on it.",
        "there are zero pubs here.",
        "there are sixty five parks.",
        "it is the fortieth quietest.",
        # The fact holds 70 and 1, and not 71: the two words are one number.
        "seventy-five areas are noisier.",
        "fifty-seven per cent of areas are noisier.",
    ],
)
def test_a_number_written_as_a_word_must_be_supported_like_any_other(text: str):
    # The noise fact holds 15, 71, 7 and the 55 of its label.
    assert reason(text, NOISE) is VerdictReason.UNSUPPORTED_NUMBER


def test_two_words_that_make_one_number_are_read_as_that_number():
    assert reason("quieter than seventy-one per cent of areas.", NOISE) is VerdictReason.OK
    assert reason("quieter than seventy one per cent of areas.", NOISE) is VerdictReason.OK
    assert reason("at fifty-five decibels or more.", NOISE) is VerdictReason.OK
    # Fifty and five are not in the fact, and neither is seventy or one.
    assert reason("fifty areas and five more.", NOISE) is VerdictReason.UNSUPPORTED_NUMBER
    assert reason("seventy areas, and one more.", NOISE) is VerdictReason.UNSUPPORTED_NUMBER


@pytest.mark.parametrize(
    "text",
    [
        "it is an hour from the coast.",
        "two hours from anywhere.",
        "a quarter of homes are flats.",
        "three quarters of it is green.",
        "two thirds of it is green.",
        "it has changed a lot in a fortnight.",
        "it has been so for a decade.",
        "the streets are over a century old.",
        "decades of building.",
        "it is a week since the market moved.",
        "the market is open every day.",
        "hundreds of venues.",
        "tens of parks and thousands of homes.",
        "it was so a year ago.",
    ],
)
def test_a_length_of_time_or_a_fraction_said_in_words_always_fails(text: str):
    assert not verify(said(text, PARK, NOISE, STATION), facts()).ok


MISSPELT = [
    *("fourty", "fourtieth", "ninty", "nineth", "twelth", "eigth", "fiveteen", "fivety"),
    *("eightteen", "thirtyth", "sixtys", "seventies", "twentyone", "fortyfive", "onehundred"),
]


@pytest.mark.parametrize("word", MISSPELT)
def test_a_number_word_that_is_misspelt_or_run_together_is_still_a_number(word: str):
    # "Fourty minutes" holds no digit and no word of the list, and says forty.
    for text in (f"it is about {word} minutes from the office.", f"the {word} quietest."):
        assert reason(text, NOISE) is VerdictReason.UNSUPPORTED_NUMBER, text
        assert reason(text.capitalize(), NOISE) is not VerdictReason.OK


@pytest.mark.parametrize("word", ["nil", "naught", "zilch", "none", "nowt"])
def test_a_word_for_nothing_is_the_number_nought(word: str):
    assert reason(f"there are {word} pubs here.", NOISE) is VerdictReason.UNSUPPORTED_NUMBER
    none = {NOISE: facts()[NOISE].model_copy(update={"numbers": ("0", "7")})}
    assert verify(said(f"{word} of the 7 areas compared is quieter.", NOISE), none).ok


@pytest.mark.parametrize(
    "text",
    [
        "the station is a minute away.",
        "the park is a mile away.",
        "it is a stop from the centre.",
        "the shops are a kilometre off.",
        "a metre from the water.",
    ],
)
def test_a_unit_said_with_an_article_is_one_of_it(text: str):
    # The station fact holds a walk of 4 minutes, and no 1.
    assert facts()[STATION].numbers == ("4",)
    assert reason(text, STATION) is VerdictReason.UNSUPPORTED_NUMBER
    one = {STATION: facts()[STATION].model_copy(update={"numbers": ("1",)})}
    assert verify(said(text, STATION), one).ok


def test_a_rate_is_not_a_quantity():
    # "A month" is what a rent is paid by, and "a year" what a crime rate is counted over.
    assert reason("Rent is \u00a31,250 a month.", RENT) is VerdictReason.OK
    crime = f"{area_id(2)}/feature/crime_burglary_theft"
    found = {f.fact_id: f for f in facts_for(small_release(), area_id(2), None)}
    assert "a year" in found[crime].slots["value"]
    assert verify(said(f"Recorded at {found[crime].slots['value']}.", crime), found).ok


@pytest.mark.parametrize("numeral", ["xxi", "iv", "xii", "mmxxvi", "lx", "mix", "XXI", "Xxi"])
def test_a_roman_numeral_is_a_number(numeral: str):
    # The park fact holds 20, 57, 7 and the 2 of its label.
    for text in (f"it is {numeral} minutes from the centre.", f"the {numeral} quietest."):
        assert not verify(said(text, PARK), facts()).ok, text
    # One letter is a word or a unit: "I", and the m of 280 m.
    assert reason("I am 20 m from a park.", PARK) is VerdictReason.OK
    # And a numeral a fact holds the number of is that number.
    assert reason("it is iv minutes to the station.", STATION) is VerdictReason.OK


@pytest.mark.parametrize(
    "text",
    [
        "The station is \uff15 minutes away.",  # a full-width digit
        "The park is \u00bd a mile away.",  # a vulgar fraction
        "The shops are \u0664 minutes away.",  # an Arabic-Indic digit
        "It scores \u2463 for parks.",  # a number in a circle
        "It is \u2163 stops from the centre.",  # a Roman numeral as one character
        "It is 4\u00b2 minutes away.",  # a superscript on a number is a power
        "A walk of 4 \u00b3 minutes.",
    ],
)
def test_a_digit_that_is_not_ascii_is_a_number_nothing_can_support(text: str):
    assert reason(text, STATION) is VerdictReason.UNSUPPORTED_NUMBER
    assert reason(text) is VerdictReason.UNSUPPORTED_NUMBER


def test_a_number_said_with_the_sign_of_another_kind_of_number_is_rejected():
    found = facts()
    assert found[PARK].numbers == ("20", "57%", "7")
    # Each number is the park's own. None of them is money, and only one is a share.
    for text in (
        "Rent is \u00a357 a month.",
        "Rent is \u00a320.",
        "20% of homes.",
        "7% are closer.",
    ):
        assert reason(text, PARK) is VerdictReason.UNSUPPORTED_NUMBER, text
    assert reason("It is 20 m away, closer than 57% of the 7 areas.", PARK) is VerdictReason.OK
    # Money is money and nothing else.
    assert found[RENT].slots["upper"] == "1,400"
    assert reason("The upper end is \u00a31,400.", RENT) is VerdictReason.OK
    assert reason("The upper end is 1,400 pounds.", RENT) is VerdictReason.OK
    assert reason("1,400% of the median.", RENT) is VerdictReason.UNSUPPORTED_NUMBER
    assert reason("It costs \u00a32026.", RENT) is VerdictReason.UNSUPPORTED_NUMBER


def test_a_word_for_a_number_is_no_number_when_it_is_part_of_a_name():
    quarter = {
        f.fact_id: f.model_copy(update={"names": ("Tallow Guild Quarter", "Seven Elms")})
        for f in facts().values()
        if f.fact_id == NAME
    }
    for text in ("It is near Tallow Guild Quarter.", "Seven Elms is close by."):
        assert verify(said(text, NAME), quarter).ok, text
    # The word alone is a quantity again, whatever name holds it.
    for text in ("A Quarter of it is green.", "Seven parks are nearby.", "About seven of them."):
        assert not verify(said(text, NAME), quarter).ok, text


@pytest.mark.parametrize(
    "text", ["It is in postcode E8.", "It is in SW1A.", "Flat 4b is nearby.", "It is 20m away."]
)
def test_a_token_that_mixes_letters_and_digits_is_checked_as_a_name(text: str):
    assert not verify(said(text, NAME, PARK), facts()).ok


def test_a_number_written_as_a_word_passes_when_the_fact_holds_it():
    # The label of park proximity holds a 2, and the walk to the station is 4 minutes.
    assert reason("it is near a park of two hectares or more.", PARK) is VerdictReason.OK
    assert reason("the station is four minutes away.", STATION) is VerdictReason.OK
    assert reason("the station is five minutes away.", STATION) is VerdictReason.UNSUPPORTED_NUMBER
    assert reason("one of the seven areas compared.", PARK) is VerdictReason.UNSUPPORTED_NUMBER


@pytest.mark.parametrize("word", ["half", "double", "twice", "dozen", "couple", "several"])
def test_a_quantity_with_no_number_behind_it_always_fails(word: str):
    assert reason(f"it has {word} the parks of most areas.", PARK) is VerdictReason.VAGUE_QUANTITY


@pytest.mark.parametrize("word", sorted(BANNED_WORDS))
def test_no_sentence_may_call_a_place_safe_or_unsafe(word: str):
    crime = f"{area_id(2)}/feature/crime_burglary_theft"
    found = {f.fact_id: f for f in facts_for(small_release(), area_id(2), None)}
    for text in (f"this is a {word} area.", f"it feels {word}.", f"{word}-looking streets."):
        verdict = verify(said(text, crime), found)
        assert (verdict.ok, verdict.reason) == (False, VerdictReason.BANNED_WORD)
        assert not verify(said(text), found).ok
        assert not verify(said(text.upper(), crime), found).ok
        assert not verify(said(text.capitalize(), crime), found).ok


NOT_THE_ALPHABET = [
    ("Alderwick is a s\u0430fe place.", "a Cyrillic a"),
    ("Alderwick is a \u0455afe place.", "a Cyrillic s"),
    ("Alderwick is a saf\u0435 place.", "a Cyrillic e"),
    ("Alderwick is a r\u03bfugh place.", "a Greek o"),
    ("Alderwick is a d\u0585dgy place.", "an Armenian o"),
    ("Alderwick is a \uff53\uff41\uff46\uff45 place.", "full-width letters"),
    ("Alderwick is a \U0001d42c\U0001d41a\U0001d41f\U0001d41e place.", "mathematical bold"),
    ("Alderwick is a s\u00e1fe place.", "an accent"),
    ("Alderwick is a sa\u0301fe place.", "a combining accent"),
    ("Alderwick is a sa\u200bfe place.", "a zero-width space inside the word"),
    ("Alderwick is a sa\u00adfe place.", "a soft hyphen inside the word"),
    ("Alderwick is a sa\u2060fe place.", "a word joiner inside the word"),
    ("Alderwick is \u0405AFE.", "capitals, the first Cyrillic"),
]


@pytest.mark.parametrize(
    ("text", "written_with"), NOT_THE_ALPHABET, ids=[how for _, how in NOT_THE_ALPHABET]
)
def test_a_banned_word_is_banned_however_its_letters_are_written(text: str, written_with: str):
    # "Safe" with a Cyrillic a is no word of the list, and reads as one.
    assert "safe" not in text.casefold(), written_with
    assert not verify(said(text, NAME), facts()).ok
    assert not verify(said(text), facts()).ok


def test_a_word_in_letters_no_fact_holds_is_refused_and_one_a_fact_holds_is_not():
    # Whatever it says, nothing can account for it.
    for text in ("Alderwick has a \u043a\u0430\u0444\u0435.", "It is \u03ba\u03b1\u03bb\u03cc."):
        assert not verify(said(text, NAME), facts()).ok, text
    # A unit and a name are the fact's own letters, accents and all.
    air = f"{AREA}/feature/air_no2"
    assert reason("Nitrogen dioxide is 4 \u00b5g/m\u00b3.", air) is VerdictReason.OK
    assert not verify(said("It is 4 \u00b5g/m\u00b3.", PARK), facts()).ok
    named = {NAME: facts()[NAME].model_copy(update={"names": ("Caf\u00e9 Wexmoor", "Quillhaven")})}
    assert verify(said("Caf\u00e9 Wexmoor is in Quillhaven.", NAME), named).ok
    assert not verify(said("Caf\u00e9 Alderwick is in Quillhaven.", NAME), named).ok


INFLECTED = [
    *("safely", "unsafely", "safety", "safeness", "dangerously", "dangers", "danger"),
    *("roughly", "roughness", "roughish", "dodgily", "dodginess", "sketchily"),
]


@pytest.mark.parametrize("word", INFLECTED)
def test_a_banned_word_is_banned_in_every_form_it_takes(word: str):
    assert word in BANNED_WORDS
    for text in (f"you can walk home {word} at night.", f"Alderwick: {word}."):
        verdict = verify(said(text, NAME), facts())
        assert (verdict.ok, verdict.reason) == (False, VerdictReason.BANNED_WORD), text


def test_a_sentence_that_speaks_of_safety_is_rejected():
    # It passed until the list held every form of its words.
    assert reason("Alderwick is known for its safety.", NAME) is VerdictReason.BANNED_WORD


@pytest.mark.xfail(strict=True, reason="a known limit of the verifier: contract section 7.4")
@pytest.mark.parametrize(
    "text",
    [
        "Alderwick is a secure, low-crime, respectable place.",
        "Alderwick is crime-ridden and full of undesirable people.",
        "Alderwick has a large immigrant population.",
        "Alderwick is popular with young families.",
    ],
)
def test_a_sentence_about_residents_or_safety_is_rejected(text: str):
    # Each holds no number, no name but the area's and none of the banned
    # words, so each passes. No explainer writes such a sentence today. A
    # model would, which is why none may be attached until this test passes.
    assert not verify(said(text, NAME), facts()).ok


def test_a_word_that_only_contains_a_banned_word_is_not_banned():
    assert reason("it has a safeguarded park and rougher-hewn stone.", PARK) is (
        VerdictReason.BANNED_WORD
    )
    assert reason("it has a safeguarded park.", PARK) is VerdictReason.OK


def test_a_fact_that_is_not_among_the_areas_facts_cannot_be_cited():
    other = f"{area_id(2)}/feature/park_proximity"
    assert other in facts(area_id(2))
    assert reason("It is near a park.", other) is VerdictReason.UNKNOWN_FACT
    assert reason("It is near a park.", "syn-n0001/feature/made_up") is VerdictReason.UNKNOWN_FACT
    assert reason("It is near a park.", PARK, "") is VerdictReason.UNKNOWN_FACT


def test_a_verdict_holds_a_code_and_never_the_text():
    verdict = verify(said("Alderwick is close to Victoria Park.", NAME), facts())
    assert verdict.model_dump() == {"ok": False, "reason": VerdictReason.UNSUPPORTED_NAME}
    assert "Victoria" not in repr(verdict)


def test_the_superscript_in_a_unit_is_not_a_number():
    air = f"{AREA}/feature/air_no2"
    assert facts()[air].slots["value"] == "4 µg/m³"
    assert reason("Nitrogen dioxide is 4 µg/m³.", air) is VerdictReason.OK
    assert reason("Nitrogen dioxide is 3 µg/m³.", air) is VerdictReason.UNSUPPORTED_NUMBER
    culture = f"{AREA}/feature/culture_venues"
    assert reason("It has 6 per km² of them.", culture) is VerdictReason.OK


def every_fact() -> list[Fact]:
    release = small_release()
    found = [f for area in release.neighbourhoods for f in facts_for(release, area.area_id, spec())]
    worked = build_worked_release()
    found += [
        f
        for area in worked.neighbourhoods
        for f in facts_for(worked, area.area_id, build_worked_spec())
    ]
    return found


def test_every_template_passes_the_verifier():
    seen: set[TemplateId] = set()
    for fact in every_fact():
        sentence = render(fact)
        assert sentence.origin is SentenceOrigin.TEMPLATE
        assert sentence.fact_ids == (fact.fact_id,)
        assert "{" not in sentence.text
        verdict = verify(sentence, {fact.fact_id: fact})
        assert verdict.ok, (fact.template, verdict.reason)
        seen.add(fact.template)
    assert seen == set(TemplateId) == set(TEMPLATES)


def test_no_template_names_a_city_or_passes_judgement():
    for text in (*TEMPLATES.values(), *STANDINGS.values()):
        lowered = text.lower()
        assert "london" not in lowered
        assert not set(lowered.replace(".", " ").replace(",", " ").split()) & BANNED_WORDS
        assert not {"good", "bad", "best", "worst", "nice", "affordable", "cheap"} & set(
            lowered.replace(".", " ").split()
        )
    # A comparison is with areas of this release, and says so whichever way it is put.
    assert all("{standing}" in TEMPLATES[t] for t in (TemplateId.FEATURE, TemplateId.TAG))
    assert all(" in this release" in text for text in STANDINGS.values())


def test_a_template_sentence_fails_when_it_is_cited_to_the_wrong_fact():
    found = facts()
    sentence = render(found[PARK])
    assert verify(sentence, found).ok
    wrong = sentence.model_copy(update={"fact_ids": (NOISE,)})
    assert not verify(wrong, found).ok


def test_ordinary_words_name_nothing():
    assert {word.casefold() for word in ORDINARY_WORDS} == ORDINARY_WORDS
    names = {n.name.casefold() for n in small_release().neighbourhoods}
    names |= {p.name.casefold() for p in small_release().places}
    assert not ORDINARY_WORDS & {part for name in names for part in name.split()}
