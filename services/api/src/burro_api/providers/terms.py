"""What people are told about where their words go, and what was read of each provider's terms.

**What people are told** is a few sentences, served by the API (`notice`):
that what is typed is sent to a language model run by the company, to be
read, what goes with it, that nothing private should be typed, and that
Burro itself keeps nothing of it. With them goes the address of the
company's own terms (`terms_url`). The notice states nothing about the
company as fact: not how long it keeps words, not whether it trains on them.
Nobody has checked those, and the link serves in their place (ADR 0023). The
website and the app show what is served and write none of it themselves.

The words go alone unless the service is set to send the search settings
with them. Which of the two is so is said in every notice, and whoever makes
a notice says which: there is no default.

**The table is research, and is shown to nobody.** It holds the same
questions for every provider, each answered in one form of words (`FORMS`),
with the provider's own pages, the day they were read and how. A tool read
them. No person has compared a sentence with its page: `checked_by` and
`checked_on` are empty in every entry. Nothing of the table is served, put in
a notice or waited for. What `choose` reads of an entry is the company's
name, the variable of its key, its model and the address of its terms.

A dated snapshot. Terms change: read them again before relying on a sentence.
Nothing here is legal advice. See `docs/design/models.md`.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from types import MappingProxyType


class Provider(StrEnum):
    GEMINI = "gemini"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    ANTHROPIC = "anthropic"


class Read(StrEnum):
    """How a page reached whoever wrote the answer. It is kept as a record, and decides nothing."""

    PAGE = "page"
    # Through a tool that summarises, which can change a word or a number.
    EXTRACT = "extract"
    # An inference, a recollection, or a thing the page did not say.
    NOT_READ = "not_read"


class Question(StrEnum):
    """What is asked of every provider, in the order a person is told it."""

    RECEIVER = "receiver"
    TRAINING = "training"
    KEPT = "kept"
    BY_LAW = "by_law"
    IF_MISUSE = "if_misuse"
    READ_BY = "read_by"
    HANDLED = "handled"
    STORED = "stored"


@dataclass(frozen=True)
class Form:
    """The words for one question: where the documents answer it, and where they do not."""

    said: str
    unsaid: str


# One verb for each question, whoever is asked. `{company}` is the name a
# person knows the provider by, and `{answer}` is what its documents say.
FORMS: Mapping[Question, Form] = MappingProxyType(
    {
        Question.RECEIVER: Form(
            "When you type a sentence, Burro sends it to {company} ({answer}).",
            "When you type a sentence, Burro sends it to {company}, "
            "which does not say which of its companies receives it.",
        ),
        Question.TRAINING: Form(
            "{company} says it {answer}.",
            "{company} does not say whether it uses them to train its models.",
        ),
        Question.KEPT: Form(
            "It keeps them for {answer}.",
            "It does not say how long it keeps them.",
        ),
        Question.BY_LAW: Form(
            "It may keep them for as long as the law requires.",
            "It does not say whether it keeps them for longer where the law requires it.",
        ),
        Question.IF_MISUSE: Form(
            "If it suspects misuse, it {answer}.",
            "It does not say whether it keeps them for longer if it suspects misuse.",
        ),
        Question.READ_BY: Form(
            "They may be read by {answer}.",
            "It does not say who may read them.",
        ),
        Question.HANDLED: Form(
            "They may be handled in {answer}.",
            "It does not say where they are handled.",
        ),
        Question.STORED: Form(
            "They are stored in {answer}.",
            "It does not say where they are stored.",
        ),
    }
)


@dataclass(frozen=True)
class Answer:
    question: Question
    # What the provider's documents say, in the fewest words that fit the
    # form. `None` where the documents, as read, do not answer the question.
    answer: str | None
    # The provider's words that the answer rests on. Empty where there is none.
    rests_on: tuple[str, ...]
    # Where it was read, or where it was looked for and not found.
    addresses: tuple[str, ...]
    read_on: date
    read: Read
    # What whoever checks the sentence should know before they do.
    note: str = ""
    # Who compared the sentence with the page at each address, and on what
    # day. A person writes these, and nobody else. Empty until then.
    checked_by: str = ""
    checked_on: date | None = None

    @property
    def answered(self) -> bool:
        return self.answer is not None

    @property
    def checked(self) -> bool:
        """Whether a person has compared the sentence with its source since it was written."""
        if self.checked_on is None or not self.checked_by.strip():
            return False
        return self.checked_on >= self.read_on


@dataclass(frozen=True)
class Terms:
    provider: Provider
    # The company that receives the words, as a person would know it.
    company: str
    # The one variable its key is read from.
    key_variable: str
    # The smallest model the research found fit for the job on the day.
    model: str
    # The company's own page of terms, which people are pointed to.
    terms_url: str
    # One answer to each question, in the order of the questions. Research,
    # checked by nobody and shown to nobody.
    answers: tuple[Answer, ...]
    # What must be so for the notice to be true. For whoever turns the provider on.
    holds_if: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if tuple(answer.question for answer in self.answers) != tuple(Question):
            raise ValueError("every question is answered once, in order")

    def answer(self, question: Question) -> Answer:
        return self.answers[list(Question).index(question)]

    def says(self, question: Question) -> str:
        """What the table holds in answer to `question`, in the form every provider shares."""
        given = self.answer(question)
        form = FORMS[question]
        if given.answer is None:
            return form.unsaid.format(company=self.company)
        return form.said.format(company=self.company, answer=given.answer)

    @property
    def checked(self) -> bool:
        return all(answer.checked for answer in self.answers)

    def sent_with(self, with_settings: bool) -> str:
        """What a person is told goes with their words. It is Burro's to say, whoever receives."""
        return SETTINGS if with_settings else WORDS_ALONE

    def notice(self, with_settings: bool) -> str:
        """The whole of what a person is told, as one paragraph.

        Whose model reads the words, what goes with them, and Burro's own
        three sentences. Nothing of `answers` is in it.
        """
        return " ".join(
            (
                SENT.format(company=self.company),
                self.sent_with(with_settings),
                PRIVATE,
                KEEPS_NOTHING,
                ITS_TERMS.format(company=self.company),
            )
        )


# What goes with the words where the service is set to send the search: each
# field of a search as the reader sends it, and the words of `SETTINGS` that
# tell of it. `None` is a field that says nothing of the person. A test holds
# this to what the reader sends, so a field that is added to a search is not
# sent before people are told of it.
SENT_WITH: Mapping[str, str | None] = MappingProxyType(
    {
        "schema_version": None,
        "budget": "your budget",
        "tenure": "whether you rent or buy",
        "commutes": "how long you will travel",
        "commute_combine": "how long you will travel",
        "commute_weight": "how long you will travel",
        "pt_basis": "how long you will travel",
        "weights": "what matters to you",
        "tags": "what matters to you",
        "areas": "the areas you have ruled in or out",
    }
)
# Burro's own statement of what it sends, the same whoever receives it: where
# the search is sent with the words, and where the words go alone.
SETTINGS = (
    "With it go your search settings: your budget, whether you rent or buy, how long you "
    "will travel, what matters to you, and the areas you have ruled in or out."
)
WORDS_ALONE = "Your words go alone: none of your search settings is sent with them."
# The rest of the notice, the same whoever receives the words. It names the
# company and says nothing of what the company does.
SENT = "What you type is sent to a language model run by {company}, to be read."
PRIVATE = "Do not type anything private."
KEEPS_NOTHING = "Burro itself keeps nothing of what you type."
ITS_TERMS = "What {company} does with it is in {company}'s own terms."
# What is said when no model reads what is typed.
RULES_NOTICE = (
    "What you type is read by rules that are part of Burro. It is not sent to a language model."
)

_READ_ON = date(2026, 9, 23)
_NOT_TRAINED = "does not use them to train its models"
_AS_NEEDED = "may keep them for as long as it finds necessary, and gives no period"
# The form for this question says all there is to say.
_IT_MAY = ""


def _said(
    question: Question,
    answer: str,
    rests_on: tuple[str, ...],
    addresses: tuple[str, ...],
    read: Read,
    note: str = "",
) -> Answer:
    return Answer(question, answer, rests_on, addresses, _READ_ON, read, note)


def _unsaid(question: Question, looked_in: tuple[str, ...], read: Read, note: str = "") -> Answer:
    return Answer(question, None, (), looked_in, _READ_ON, read, note)


_GEMINI_TERMS = "https://ai.google.dev/gemini-api/terms"
_GEMINI_MISUSE = "https://ai.google.dev/gemini-api/docs/usage-policies"
_GOOGLE_AGREEMENT = "https://business.safety.google/processorterms/"
_ANY_COUNTRY = "any country where Google or its agents have facilities"
_ANY_COUNTRY_WORDS = (
    "This data may be stored transiently or cached in any country in which Google or its "
    "agents maintain facilities.",
    "Google may process Partner Personal Data in any country in which Google or its "
    "Subprocessors maintain facilities.",
)

_GEMINI = Terms(
    provider=Provider.GEMINI,
    company="Google",
    key_variable="GEMINI_API_KEY",
    model="gemini-3.5-flash-lite",
    terms_url=_GEMINI_TERMS,
    answers=(
        _said(
            Question.RECEIVER,
            "Google LLC, United States",
            (
                '"Google" means Google LLC, with offices at 1600 Amphitheatre Parkway, '
                "Mountain View, California 94043, United States, unless set forth otherwise "
                "in additional terms applicable for a given API.",
            ),
            ("https://developers.google.com/terms", _GEMINI_TERMS),
            Read.EXTRACT,
            note=(
                "The Gemini API's own terms, as read, name no other company. The agreement on "
                "data processing says a Google entity is 'Google LLC, Google Ireland Limited "
                "or any other Affiliate of Google LLC'."
            ),
        ),
        _said(
            Question.TRAINING,
            _NOT_TRAINED,
            (
                "Google doesn't use your prompts (including associated system instructions, "
                "cached content, and files such as images, videos, or documents) or responses "
                "to improve our products",
            ),
            (_GEMINI_TERMS,),
            Read.EXTRACT,
            note="Said of Paid Services. The same page says the opposite of unpaid ones.",
        ),
        _said(
            Question.KEPT,
            "55 days",
            (
                "Google retains the following data for fifty-five (55) days for the purposes of "
                "detecting and preventing violations of the Prohibited Use Policy",
            ),
            (_GEMINI_MISUSE,),
            Read.EXTRACT,
        ),
        _said(
            Question.BY_LAW,
            _IT_MAY,
            (
                "Google will delete such Partner Personal Data from its systems as soon as "
                "reasonably practicable, unless applicable laws require storage.",
            ),
            (_GOOGLE_AGREEMENT,),
            Read.EXTRACT,
            note=(
                "From the agreement on data processing, section 6.1.1. The page on the 55 days "
                "does not say whether they can become more."
            ),
        ),
        _unsaid(Question.IF_MISUSE, (_GEMINI_MISUSE,), Read.EXTRACT),
        _said(
            Question.READ_BY,
            "its staff, if it suspects misuse",
            (
                "authorized Google employees may assess the flagged content",
                "Data can be accessed for human review only by authorized Google employees via "
                "an internal governance assessment and review management platform.",
            ),
            (_GEMINI_MISUSE,),
            Read.EXTRACT,
        ),
        _said(
            Question.HANDLED,
            _ANY_COUNTRY,
            _ANY_COUNTRY_WORDS,
            (_GEMINI_TERMS, _GOOGLE_AGREEMENT),
            Read.EXTRACT,
        ),
        _said(
            Question.STORED,
            _ANY_COUNTRY,
            _ANY_COUNTRY_WORDS[:1],
            (_GEMINI_TERMS,),
            Read.EXTRACT,
            note=(
                "The provider's words are of data 'stored transiently or cached'. No page read "
                "says where what is kept for 55 days is held."
            ),
        ),
    ),
    holds_if=(
        "The key belongs to a project with billing on. "
        "Google's terms allow no other for people in the UK.",
        "Logging of calls is left off in the project.",
    ),
)

_OPENAI_TERMS = "https://openai.com/policies/services-agreement/"
_OPENAI_DATA = "https://developers.openai.com/api/docs/guides/your-data"
_OPENAI_AGREEMENT = "https://openai.com/policies/data-processing-addendum/"
_OPENAI_READ_ONCE = (
    "The first reading was of the page as served. openai.com was not read again on the "
    "day, so these words were not seen a second time."
)
_OPENAI_LOGS = (
    "By default, abuse monitoring logs are generated for all API feature usage and "
    "retained for up to 30 days, unless longer retention is required by law, or is "
    "reasonably necessary to protect our services or any third party from harm."
)

_OPENAI = Terms(
    provider=Provider.OPENAI,
    company="OpenAI",
    key_variable="OPENAI_API_KEY",
    model="gpt-6-luna",
    terms_url=_OPENAI_TERMS,
    answers=(
        _said(
            Question.RECEIVER,
            "OpenAI OpCo, LLC, United States",
            (
                "OpenAI OpCo, LLC, for Customers located outside the EEA or Switzerland",
                "Data importer(s): OpenAI OpCo, LLC, 1455 3rd Street, San Francisco, CA 94158",
            ),
            (_OPENAI_TERMS, _OPENAI_AGREEMENT),
            Read.PAGE,
            note=_OPENAI_READ_ONCE,
        ),
        _said(
            Question.TRAINING,
            _NOT_TRAINED,
            (
                "As of March 1, 2023, data sent to the OpenAI API is not used to train or improve "
                "OpenAI models (unless you explicitly opt in to share data with us).",
            ),
            (_OPENAI_DATA,),
            Read.PAGE,
        ),
        _said(Question.KEPT, "up to 30 days", (_OPENAI_LOGS,), (_OPENAI_DATA,), Read.PAGE),
        _said(Question.BY_LAW, _IT_MAY, (_OPENAI_LOGS,), (_OPENAI_DATA,), Read.PAGE),
        _said(
            Question.IF_MISUSE,
            _AS_NEEDED,
            (_OPENAI_LOGS,),
            (_OPENAI_DATA,),
            Read.PAGE,
            note=(
                "The provider's words are wider than misuse: 'reasonably necessary to protect "
                "our services or any third party from harm'."
            ),
        ),
        _said(
            Question.READ_BY,
            "its staff, and by contractors who look into misuse",
            (
                "Our access to API business data stored on our systems is limited to "
                "(1) authorized employees that require access for engineering support, "
                "investigating potential platform abuse, and legal compliance and "
                "(2) specialized third-party contractors who are bound by confidentiality and "
                "security obligations, solely to review for abuse and misuse.",
            ),
            ("https://openai.com/enterprise-privacy/",),
            Read.PAGE,
            note=_OPENAI_READ_ONCE,
        ),
        _unsaid(
            Question.HANDLED,
            (_OPENAI_DATA, _OPENAI_AGREEMENT, "https://openai.com/policies/sub-processor-list/"),
            Read.PAGE,
            note=(
                "No page read names the countries where a call is handled unless a region is "
                "agreed with the provider. The list of sub-processors names companies in many "
                "countries. " + _OPENAI_READ_ONCE
            ),
        ),
        _unsaid(
            Question.STORED,
            (_OPENAI_DATA, _OPENAI_AGREEMENT),
            Read.PAGE,
            note="As for where they are handled.",
        ),
    ),
    holds_if=(
        "`store` is false on every call, which the adapter sees to.",
        "Sharing of data with the provider is left off in its dashboard.",
        "Whoever runs Burro is outside the EEA and Switzerland. "
        "Inside them the provider's company is another.",
    ),
)

_DEEPSEEK_USE = "https://cdn.deepseek.com/policies/en-US/deepseek-terms-of-use.html"
_DEEPSEEK_PRIVACY = "https://cdn.deepseek.com/policies/en-US/deepseek-privacy-policy.html"
_DEEPSEEK_PLATFORM = (
    "https://cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html"
)
_DEEPSEEK_SCOPE = (
    "The privacy policy says it does not cover people who use a product built on the "
    "provider's API. The terms for the API say nothing on this question."
)
_IN_CHINA = (
    "we directly collect, process and store your Personal Data in People's Republic of China",
)

_DEEPSEEK = Terms(
    provider=Provider.DEEPSEEK,
    company="DeepSeek",
    key_variable="DEEPSEEK_API_KEY",
    model="deepseek-flash",
    terms_url=_DEEPSEEK_PLATFORM,
    answers=(
        _said(
            Question.RECEIVER,
            "Hangzhou DeepSeek Artificial Intelligence Co., Ltd., China",
            (
                "The DeepSeek Open Platform is owned and operated by Hangzhou DeepSeek "
                "Artificial Intelligence Co., Ltd.",
                "The Services are provided and controlled by Hangzhou DeepSeek Artificial "
                "Intelligence Co., Ltd., with its registered address in China.",
            ),
            (_DEEPSEEK_PLATFORM, _DEEPSEEK_PRIVACY),
            Read.EXTRACT,
        ),
        _said(
            Question.TRAINING,
            "may use them to improve its service and the technology under it, to a minimal "
            "extent and with what identifies a person taken out. Its documents name no way "
            "for a service like Burro to refuse",
            (
                "Under the premise of secure encryption technology processing, strict "
                "de-identification rendering, and irreversibility to identify specific "
                "individuals, we may, to a minimal extent, use Inputs and Outputs to provide, "
                "maintain, operate, develop or improve the Services or the underlying "
                "technologies supporting the Services.",
                "If you refuse to allow us to process the data in the manner described above, "
                "you can opt out by turning off 'Improve the model for everyone'.",
            ),
            (_DEEPSEEK_USE, _DEEPSEEK_PLATFORM),
            Read.EXTRACT,
            note=(
                "The terms name a switch. No page read says where it is or whether it reaches "
                "the API. The terms for the API do not speak of training."
            ),
        ),
        _unsaid(
            Question.KEPT,
            (_DEEPSEEK_PRIVACY, _DEEPSEEK_PLATFORM),
            Read.EXTRACT,
            note=(
                "The privacy policy gives no period: 'We retain Personal Data for as long as "
                "necessary to provide our Services and for the other purposes set out in this "
                "Privacy Policy.' " + _DEEPSEEK_SCOPE
            ),
        ),
        _said(
            Question.BY_LAW,
            _IT_MAY,
            (
                "We also retain Personal Data when necessary to comply with contractual and "
                "legal obligations, when we have a legitimate business interest to do so.",
            ),
            (_DEEPSEEK_PRIVACY,),
            Read.EXTRACT,
            note=_DEEPSEEK_SCOPE,
        ),
        _said(
            Question.IF_MISUSE,
            _AS_NEEDED,
            (
                "If you violate any of our terms, policies or guidelines, we may keep your "
                "Personal Data as necessary to process the violation.",
            ),
            (_DEEPSEEK_PRIVACY,),
            Read.EXTRACT,
            note=_DEEPSEEK_SCOPE,
        ),
        _unsaid(
            Question.READ_BY,
            (_DEEPSEEK_PRIVACY, _DEEPSEEK_PLATFORM),
            Read.EXTRACT,
            note=(
                "The privacy policy says service providers and companies of its group 'will "
                "access, process, or store Personal Data only in the course of performing their "
                "duties to us', and that data may be shared with public authorities. It does "
                "not say who may read what was sent. " + _DEEPSEEK_SCOPE
            ),
        ),
        _said(
            Question.HANDLED,
            "China",
            _IN_CHINA,
            (_DEEPSEEK_PRIVACY,),
            Read.EXTRACT,
            note=_DEEPSEEK_SCOPE,
        ),
        _said(
            Question.STORED,
            "China",
            _IN_CHINA,
            (_DEEPSEEK_PRIVACY,),
            Read.EXTRACT,
            note=_DEEPSEEK_SCOPE,
        ),
    ),
    holds_if=(
        "The provider's privacy policy is taken to describe what reaches it through its API, "
        "though it says it does not cover people who use a product built on it. "
        "No other document of the provider's speaks of them.",
    ),
)

_ANTHROPIC_TERMS = "https://www.anthropic.com/legal/commercial-terms"
_ANTHROPIC_AGREEMENT = "https://www.anthropic.com/legal/data-processing-addendum"
_ANTHROPIC_KEPT = (
    "https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data"
)
_ANTHROPIC_WHERE = (
    "https://privacy.claude.com/en/articles/"
    "7996890-where-are-your-servers-located-do-you-host-your-models-on-eu-servers"
)

_ANTHROPIC = Terms(
    provider=Provider.ANTHROPIC,
    company="Anthropic",
    key_variable="ANTHROPIC_API_KEY",
    model="claude-haiku-4-5-20251001",
    terms_url=_ANTHROPIC_TERMS,
    answers=(
        _said(
            Question.RECEIVER,
            "Anthropic Ireland, Limited, Ireland",
            (
                '"Anthropic" means Anthropic Ireland, Limited if Customer resides in the '
                'European Economic Area ("EEA"), Switzerland or UK',
            ),
            (_ANTHROPIC_TERMS,),
            Read.PAGE,
            note="For a customer who resides anywhere else the terms name Anthropic, PBC.",
        ),
        _said(
            Question.TRAINING,
            _NOT_TRAINED,
            ("Anthropic may not train models on Customer Content from Services.",),
            (_ANTHROPIC_TERMS,),
            Read.PAGE,
        ),
        _said(
            Question.KEPT,
            "up to 30 days",
            (
                "we automatically delete inputs and outputs on our backend within 30 days of "
                "receipt or generation",
            ),
            (_ANTHROPIC_KEPT,),
            Read.PAGE,
            note=(
                "Another of the provider's pages says text 'is not retained by default'. It "
                "points to this one for the periods."
            ),
        ),
        _said(
            Question.BY_LAW,
            _IT_MAY,
            ("In compliance with the law",),
            (_ANTHROPIC_KEPT,),
            Read.EXTRACT,
            note="One of the exceptions the page lists to the 30 days.",
        ),
        _said(
            Question.IF_MISUSE,
            "keeps them for up to 2 years, and its safety scores for up to 7 years",
            (
                "We retain inputs and outputs for up to 2 years and trust and safety "
                "classification scores for up to 7 years if your chat is flagged by our "
                "automated trust and safety systems as violating our Usage Policy.",
            ),
            (_ANTHROPIC_KEPT,),
            Read.PAGE,
            note=(
                "The page also lists enforcing the Usage Policy among its exceptions to the "
                "30 days, and gives no period for it."
            ),
        ),
        _unsaid(
            Question.READ_BY,
            (
                _ANTHROPIC_KEPT,
                _ANTHROPIC_WHERE,
                _ANTHROPIC_TERMS,
                _ANTHROPIC_AGREEMENT,
                "https://privacy.claude.com/en/collections/10663361-commercial-customers",
            ),
            Read.EXTRACT,
            note=(
                "The agreement on data processing says each person authorised to process is "
                "under a duty of confidentiality. The page on where data is handled names "
                "'safety-related review' as one of the provider's internal processes. Neither "
                "says who may read what was sent. No article listed for commercial customers "
                "is about it."
            ),
        ),
        _said(
            Question.HANDLED,
            "the United States, Europe, Asia and Australia, and wherever it or its affiliates work",
            (
                "By default, we may route customer traffic to select countries in the US, "
                "Europe, Asia and Australia, unless otherwise agreed upon or at your "
                "instructions.",
                "We may also process data for internal processes (such as safety-related "
                "review, product support, or incident response) in countries where we or our "
                "affiliates operate.",
            ),
            (_ANTHROPIC_WHERE,),
            Read.PAGE,
        ),
        _said(
            Question.STORED,
            "the United States",
            ("Note that data is stored in the US.",),
            (_ANTHROPIC_WHERE,),
            Read.PAGE,
        ),
    ),
    holds_if=(
        "The Development Partner Program is left off.",
        "No real sentence is pasted into the provider's console, and no feedback is sent from it.",
        "Whoever runs Burro resides in the UK, the EEA or Switzerland. "
        "Elsewhere the provider's company is another.",
    ),
)

TERMS: Mapping[Provider, Terms] = MappingProxyType(
    {entry.provider: entry for entry in (_GEMINI, _OPENAI, _DEEPSEEK, _ANTHROPIC)}
)
