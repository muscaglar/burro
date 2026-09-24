"""What people are told of a provider, and the table of its terms, which is shown to nobody."""

import re
from dataclasses import replace
from datetime import date, timedelta
from urllib.parse import urlsplit

import pytest
from burro_api.providers.choose import ADAPTERS
from burro_api.providers.terms import (
    FORMS,
    ITS_TERMS,
    KEEPS_NOTHING,
    PRIVATE,
    RULES_NOTICE,
    SENT,
    SENT_WITH,
    SETTINGS,
    TERMS,
    WORDS_ALONE,
    Answer,
    Provider,
    Question,
    Read,
    Terms,
)

each = pytest.mark.parametrize("terms", TERMS.values(), ids=lambda terms: terms.provider.value)
every_question = pytest.mark.parametrize("question", Question, ids=lambda question: question.value)

# The provider's own hosts. A sentence rests on what the provider says, and
# on nothing that is said about it.
OWN_HOSTS = {
    Provider.GEMINI: {"ai.google.dev", "developers.google.com", "business.safety.google"},
    Provider.OPENAI: {"developers.openai.com", "openai.com"},
    Provider.DEEPSEEK: {"cdn.deepseek.com"},
    Provider.ANTHROPIC: {"www.anthropic.com", "privacy.claude.com"},
}
KEY_VARIABLES = {
    Provider.GEMINI: "GEMINI_API_KEY",
    Provider.OPENAI: "OPENAI_API_KEY",
    Provider.DEEPSEEK: "DEEPSEEK_API_KEY",
    Provider.ANTHROPIC: "ANTHROPIC_API_KEY",
}
A_PERSON = "A. Person"


def checked(answer: Answer, on: date | None = None) -> Answer:
    return replace(answer, checked_by=A_PERSON, checked_on=on or answer.read_on)


def all_checked(terms: Terms) -> Terms:
    return replace(terms, answers=tuple(checked(answer) for answer in terms.answers))


def shape(terms: Terms, question: Question) -> str:
    """A sentence with the provider's name taken out, to set beside another provider's."""
    return terms.says(question).replace(terms.company, "X")


def test_there_is_one_entry_for_each_provider_and_no_other():
    assert list(TERMS) == list(Provider) == list(ADAPTERS)
    assert all(terms.provider is provider for provider, terms in TERMS.items())
    assert [provider.value for provider in Provider] == [
        "gemini",
        "openai",
        "deepseek",
        "anthropic",
    ]


def test_the_questions_are_these_eight_in_this_order():
    assert [question.value for question in Question] == [
        "receiver",
        "training",
        "kept",
        "by_law",
        "if_misuse",
        "read_by",
        "handled",
        "stored",
    ]
    assert set(FORMS) == set(Question)


@each
def test_every_provider_is_asked_every_question_in_the_same_order(terms: Terms):
    assert [answer.question for answer in terms.answers] == list(Question)
    assert all(terms.answer(question).question is question for question in Question)


@pytest.mark.parametrize("left_out", range(len(Question)))
def test_an_entry_that_leaves_a_question_out_cannot_be_made(left_out: int):
    whole = TERMS[Provider.ANTHROPIC]
    fewer = whole.answers[:left_out] + whole.answers[left_out + 1 :]

    with pytest.raises(ValueError, match="every question is answered once"):
        replace(whole, answers=fewer)
    # Nor one that answers a question twice, or in an order of its own.
    with pytest.raises(ValueError, match="every question is answered once"):
        replace(whole, answers=(*whole.answers, whole.answers[left_out]))
    with pytest.raises(ValueError, match="every question is answered once"):
        replace(whole, answers=whole.answers[1:] + whole.answers[:1])


@each
def test_every_answer_says_where_it_was_read_and_when_and_how(terms: Terms):
    for answer in terms.answers:
        assert answer.addresses, answer.question
        for address in answer.addresses:
            parts = urlsplit(address)
            assert parts.scheme == "https" and parts.hostname in OWN_HOSTS[terms.provider]
            assert not parts.query and not parts.username and not parts.fragment
        assert date(2026, 9, 1) <= answer.read_on <= date(2026, 9, 23)
        assert answer.read in (Read.PAGE, Read.EXTRACT, Read.NOT_READ)


@each
def test_an_answer_rests_on_the_providers_own_words_or_says_there_are_none(terms: Terms):
    for answer in terms.answers:
        if answer.answered:
            # Words of the provider's, as they stand on its page.
            assert answer.rests_on, answer.question
            assert all(quoted and quoted.strip() == quoted for quoted in answer.rests_on)
        else:
            # Nothing is put in a provider's mouth, and nothing is inferred.
            assert answer.answer is None and answer.rests_on == ()
            assert "does not say" in terms.says(answer.question)


@each
@every_question
def test_every_sentence_is_in_the_form_its_question_has_for_every_provider(
    terms: Terms, question: Question
):
    given = terms.answer(question)
    form = FORMS[question]
    said = terms.says(question)

    if given.answer is None:
        assert said == form.unsaid.format(company=terms.company)
    else:
        assert said == form.said.format(company=terms.company, answer=given.answer)
    assert said.endswith(".") and "  " not in said


def test_the_forms_have_one_verb_each_and_say_an_absence_in_one_way():
    # To keep is to keep, whoever does it. No provider "deletes within" a
    # time while another "keeps for" it.
    assert FORMS[Question.KEPT].said == "It keeps them for {answer}."
    assert "keep" in FORMS[Question.BY_LAW].said and "keep" in FORMS[Question.IF_MISUSE].unsaid
    for form in FORMS.values():
        assert "does not say" in form.unsaid and "{answer}" not in form.unsaid
    for terms in TERMS.values():
        said = " ".join(terms.says(question) for question in Question)
        assert "delete" not in said.lower() and "retain" not in said.lower()
        # What a provider's documents lack is said as a lack of theirs, and
        # never as a thing the provider has refused.
        for lack in re.findall(r"[^.]*\bno way\b[^.]*\.", said):
            assert "Its documents name no way" in lack
        assert "refuses to" not in said.lower() and "will not let" not in said.lower()


@every_question
def test_where_two_providers_say_the_same_they_are_told_of_in_the_same_words(question: Question):
    shapes = {terms.provider: shape(terms, question) for terms in TERMS.values()}
    unsaid = FORMS[question].unsaid.replace("{company}", "X")

    # Every lack is worded alike.
    lacking = {shapes[p] for p, terms in TERMS.items() if not terms.answer(question).answered}
    assert lacking <= {unsaid}
    # And every answer opens as the form does.
    opening = FORMS[question].said.replace("{company}", "X").split("{answer}")[0]
    assert all(
        shapes[p].startswith(opening)
        for p, terms in TERMS.items()
        if terms.answer(question).answered
    )


def test_the_three_that_say_they_do_not_train_are_told_of_alike():
    same = {shape(TERMS[p], Question.TRAINING) for p in Provider if p is not Provider.DEEPSEEK}

    assert same == {"X says it does not use them to train its models."}


def test_who_receives_the_words_is_said_with_its_country_for_all_four():
    # Not the country of two and the trade name of the other two.
    for terms in TERMS.values():
        first = terms.says(Question.RECEIVER)
        assert re.fullmatch(
            rf"When you type a sentence, Burro sends it to {terms.company} "
            r"\([A-Z][A-Za-z ,.]+, (United States|Ireland|China)\)\.",
            first,
        ), first


def test_a_longer_time_by_law_is_asked_of_all_four_and_not_said_of_one_alone():
    said = [terms.says(Question.BY_LAW) for terms in TERMS.values()]

    assert all(
        sentence in (FORMS[Question.BY_LAW].said, FORMS[Question.BY_LAW].unsaid)
        for sentence in said
    )
    # Anthropic's page lists the law among its exceptions, as OpenAI's does.
    assert TERMS[Provider.ANTHROPIC].answer(Question.BY_LAW).rests_on == (
        "In compliance with the law",
    )
    assert shape(TERMS[Provider.ANTHROPIC], Question.BY_LAW) == shape(
        TERMS[Provider.OPENAI], Question.BY_LAW
    )


def test_who_may_read_is_asked_of_all_four():
    for terms in TERMS.values():
        said = terms.says(Question.READ_BY)
        assert (
            said.startswith("They may be read by ") or said == "It does not say who may read them."
        )


def test_a_provider_is_told_of_in_words_no_harder_than_its_own():
    training = TERMS[Provider.DEEPSEEK].answer(Question.TRAINING)
    said = TERMS[Provider.DEEPSEEK].says(Question.TRAINING)

    # Its terms say "to a minimal extent", and so does the notice.
    assert any("to a minimal extent" in quoted for quoted in training.rests_on)
    assert "to a minimal extent" in said
    # Its terms name a way to refuse. What no page says is that it reaches a
    # service like Burro, and that is all the notice says is lacking.
    assert any("opt out" in quoted for quoted in training.rests_on)
    assert "Its documents name no way for a service like Burro to refuse." in said
    assert "give a service like Burro no way" not in said
    # Whoever checks the sentence is told of the switch.
    assert "switch" in training.note


@each
def test_a_note_says_that_a_page_was_not_read_and_not_what_a_site_answered(terms: Terms):
    # What a site answers to a program may be said by whatever stands between the two.
    answered = re.compile(r"\b(answered|returned|refused)\b|\b[345]\d\d\b")

    assert [answer.note for answer in terms.answers if answered.search(answer.note)] == []


@each
def test_the_notice_is_a_few_plain_sentences_and_ends_at_the_companys_own_terms(terms: Terms):
    sent = f"What you type is sent to a language model run by {terms.company}, to be read."
    its_terms = f"What {terms.company} does with it is in {terms.company}'s own terms."

    assert (SENT.format(company=terms.company), PRIVATE) == (sent, "Do not type anything private.")
    assert KEEPS_NOTHING == "Burro itself keeps nothing of what you type."
    assert ITS_TERMS.format(company=terms.company) == its_terms
    for with_settings, goes in ((True, SETTINGS), (False, WORDS_ALONE)):
        assert terms.notice(with_settings) == " ".join(
            [sent, goes, PRIVATE, KEEPS_NOTHING, its_terms]
        )
    assert terms.sent_with(True) == SETTINGS and terms.sent_with(False) == WORDS_ALONE


@each
@pytest.mark.parametrize("with_settings", [False, True])
def test_the_notice_states_nothing_about_the_company_as_fact(terms: Terms, with_settings: bool):
    # Nobody has checked what a provider's pages say, so none of it is said:
    # not how long words are kept, not whether they are used to train, not
    # who may read them or where. The link to the company's own terms serves.
    notice = terms.notice(with_settings)

    for question in Question:
        assert terms.says(question) not in notice
        given = terms.answer(question).answer
        assert not given or given not in notice, question
    unsaid = r"\b\d+\b|\b(days?|years?|train|kept|keeps|stored|handled|staff|law|misuse)\b"
    assert re.findall(unsaid, notice.replace(KEEPS_NOTHING, ""), flags=re.IGNORECASE) == []
    # The company is named, and nothing else of it: no legal name and no country.
    assert notice.count(terms.company) == 3
    assert not re.search(r"\b(LLC|Ltd|Limited|United States|Ireland|China)\b", notice)


@each
def test_the_link_is_to_a_page_of_the_companys_own_terms_that_the_table_read(terms: Terms):
    parts = urlsplit(terms.terms_url)

    assert parts.scheme == "https" and parts.hostname in OWN_HOSTS[terms.provider]
    assert not parts.query and not parts.username and not parts.fragment
    assert "terms" in terms.terms_url or "agreement" in terms.terms_url
    # One of the pages the table was read on, and not an address made up for the link.
    assert terms.terms_url in {a for answer in terms.answers for a in answer.addresses}
    # The address is served beside the notice, and is no part of its words.
    assert "http" not in terms.notice(with_settings=False)


def test_no_entry_of_the_table_has_been_checked_by_a_person():
    # The table is research that a tool read. It is marked as unchecked, and
    # nothing of it is served. Whoever checks an entry changes this with it.
    assert not any(answer.checked for terms in TERMS.values() for answer in terms.answers)
    assert not any(terms.checked for terms in TERMS.values())


def test_the_notice_says_that_the_search_goes_with_the_words_where_it_does():
    assert SETTINGS.startswith("With it go your search settings: ")
    for told in ("your budget", "the areas you have ruled in or out", "how long you will travel"):
        assert told in SETTINGS
    # Each thing the table says is sent is a thing the sentence names.
    assert all(told is None or told in SETTINGS for told in SENT_WITH.values())
    assert [name for name, told in SENT_WITH.items() if told is None] == ["schema_version"]
    for terms in TERMS.values():
        assert SETTINGS in terms.notice(with_settings=True)
        assert WORDS_ALONE not in terms.notice(with_settings=True)
        assert "sends your words to" not in terms.notice(with_settings=True)


def test_the_notice_says_that_the_words_go_alone_where_they_do():
    assert WORDS_ALONE == "Your words go alone: none of your search settings is sent with them."
    for terms in TERMS.values():
        notice = terms.notice(with_settings=False)
        assert WORDS_ALONE in notice and SETTINGS not in notice
        # Nothing of a search is said to go, by any of the words that tell of one.
        told = {told for told in SENT_WITH.values() if told is not None}
        assert not [words for words in told if words in notice]


def test_which_notice_is_made_is_never_left_to_a_default():
    # Whoever makes a notice says whether the settings go. A default would be
    # a sentence about what is sent that nobody chose.
    with pytest.raises(TypeError):
        TERMS[Provider.GEMINI].notice()  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        TERMS[Provider.GEMINI].sent_with()  # type: ignore[call-arg]


@each
@pytest.mark.parametrize("with_settings", [False, True])
def test_the_notice_is_plain(terms: Terms, with_settings: bool):
    notice = terms.notice(with_settings)
    assert "!" not in notice and "  " not in notice and "\n" not in notice
    assert notice.isascii()
    assert len(notice) < 400
    sentences = [sentence for sentence in re.split(r"(?<=\.) (?=[A-Z])", notice) if sentence]
    assert len(sentences) == 5
    assert all(len(sentence.split()) <= 32 for sentence in sentences)
    unwanted = ("seamless", "powerful", "cutting-edge", "state-of-the-art", "leading", "trusted")
    assert not any(word in notice.lower() for word in unwanted)


@each
def test_the_key_is_read_from_one_variable_and_the_model_is_one_the_adapter_takes(terms: Terms):
    assert terms.key_variable == KEY_VARIABLES[terms.provider]
    assert ADAPTERS[terms.provider].takes(terms.model)
    others = [other.model for other in TERMS.values() if other is not terms]
    assert not any(ADAPTERS[terms.provider].takes(model) for model in others)


def test_an_answer_is_checked_only_when_a_person_has_said_who_and_when():
    answer = replace(TERMS[Provider.OPENAI].answer(Question.KEPT), checked_by="", checked_on=None)
    day = answer.read_on

    assert not answer.checked
    assert not replace(answer, checked_by=A_PERSON).checked
    assert not replace(answer, checked_on=day).checked
    assert not replace(answer, checked_by="  ", checked_on=day).checked
    assert replace(answer, checked_by=A_PERSON, checked_on=day).checked
    assert replace(answer, checked_by=A_PERSON, checked_on=day + timedelta(days=30)).checked
    # A check that was made before the sentence was written is of another sentence.
    assert not replace(answer, checked_by=A_PERSON, checked_on=day - timedelta(days=1)).checked


@pytest.mark.parametrize("read", Read)
def test_how_a_page_was_reached_decides_nothing(read: Read):
    # All four are held to the same: a person's own look at the page. The
    # tool a page came back through on the day says nothing of the provider.
    answer = replace(
        TERMS[Provider.GEMINI].answer(Question.KEPT), read=read, checked_by="", checked_on=None
    )

    assert not answer.checked
    assert checked(answer).checked


@each
@every_question
def test_an_entry_is_checked_only_if_every_answer_of_it_is(terms: Terms, question: Question):
    whole = all_checked(terms)
    assert whole.checked

    but_one = tuple(
        replace(answer, checked_by="", checked_on=None) if answer.question is question else answer
        for answer in whole.answers
    )

    assert not replace(whole, answers=but_one).checked


@each
def test_a_lack_is_checked_like_any_other_answer(terms: Terms):
    # "It does not say" is a statement about the provider's documents too.
    whole = all_checked(terms)
    lacking = [answer for answer in whole.answers if not answer.answered]

    for answer in lacking:
        assert answer.addresses
        but_one = tuple(
            replace(given, checked_by="", checked_on=None) if given is answer else given
            for given in whole.answers
        )
        assert not replace(whole, answers=but_one).checked


@each
def test_a_check_that_is_written_down_is_whole_and_is_a_persons(terms: Terms):
    # Whatever has been checked by the day this runs. It says nothing of
    # which providers have been: that is for whoever checks them.
    for answer in terms.answers:
        assert (answer.checked_on is None) == (answer.checked_by.strip() == ""), answer.question
        if answer.checked_on is not None:
            assert answer.read_on <= answer.checked_on <= date.today()
            tools = ("claude", "gpt", "gemini", "deepseek", "assistant")
            assert not any(tool in answer.checked_by.lower() for tool in tools)


def test_the_table_cannot_be_changed_by_whoever_is_handed_it():
    with pytest.raises(TypeError):
        TERMS[Provider.GEMINI] = TERMS[Provider.OPENAI]  # type: ignore[index]
    with pytest.raises(AttributeError):
        TERMS[Provider.GEMINI].company = "Another"  # type: ignore[misc]
    with pytest.raises(TypeError):
        FORMS[Question.KEPT] = FORMS[Question.STORED]  # type: ignore[index]
    with pytest.raises(TypeError):
        SENT_WITH["budget"] = None  # type: ignore[index]


def test_what_is_said_when_no_model_reads_names_no_provider():
    assert not any(terms.company in RULES_NOTICE for terms in TERMS.values())
    assert "not sent to a language model" in RULES_NOTICE
