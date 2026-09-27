# 0044. A person who has signed in may keep a search, and what is kept is the spec and never the words

Status: accepted, 2026-09-26, as groundwork. The founder asked for it: "We'd need to store user preferences/previous searches etc and re-present this etc." It amends [0011](0011-nothing-is-kept-for-a-search.md), which kept nothing for a search, and [0005](0005-raw-prompts-are-never-stored.md), where it said that a share is the one place a spec is stored. It rests on [0043](0043-burro-has-accounts-and-a-person-signs-in-by-a-link-sent-by-email.md), and is off until accounts are turned on. Whether a person's last searches are kept from the start, and how long anything is kept, are the founder's to decide.

## Context

- [0011](0011-nothing-is-kept-for-a-search.md) decided that the server holds no search between requests. The client holds the spec and sends it again, and a share is the only stored spec. It named what would change it: "Accounts. A saved search then belongs to someone who is signed in, is reached with their session and not by an id in a URL, and is deleted with their account."
- [The design of the paid tier](../design/premium.md), section 4.4, said the same: "A saved search is a new decision. It would hold a spec, and so a workplace, for an account." This is that decision.
- A spec is small, and says a great deal: the places a person must reach, which are where they work or where their child goes to school, what they can pay, and what matters to them, a place of worship among it.
- What a person types says more than the spec made from it. People say why they want a thing: their health, their family, their religion ([0005](0005-raw-prompts-are-never-stored.md)).
- A shared search is opened by whoever holds its link, so the places of a share are replaced by the station or district that stands in for them. A search that is kept is shown to the person who kept it, and to nobody else.

## Decision

**A person who has signed in may keep a search, and may let Burro keep their last ten. What is kept of a search is the spec. What was typed is never kept, and nor is anything worked out from it but the spec.**

| Matter | What is so |
|---|---|
| A search that is kept | The spec, as the reducer left it, the release it was made on, and a name. A person presses to keep one, and may keep a hundred |
| The last searches | The last ten of an account, each held as a kept search is. The older go as the newer come |
| The name of a search | Worked out from the spec, by code: what was understood, said in a line. It is never words that a person typed, and a person cannot type one. It names what the search holds by the names the release gives, the places its journeys lead to among them: so the name says where somebody goes, as the spec beside it does |
| The places of a search | As the person named them. A share makes them coarse, because anyone may open it. A kept search is the person's own |
| What is never kept | What was typed, where its words stood, what was offered and not chosen, and the ranking. A ranking is worked out again from the spec, on the release of the day ([0002](0002-deterministic-core.md)) |
| A preference | A key from a closed list, and a value that is checked for that key. No key takes words |
| Where a person is signed in | For each session: when it was made and last used, when it ends, and the family of the browser, coarsely, so that a person knows one from another. Never the address of a client |
| What happened to an account | An event from a closed list, how it ended, and when. A person can see it, and it goes when the account goes |
| Whose rows are read and written | Is decided by the session, at the service, and never by anything a request says. Every look-up names the account, so an id that is guessed gives nothing, and says nothing of whether it is anybody's. A search or a session is named in a body, and never in a path |
| Before a spec is kept, and when it is read | It is checked by the schema that the ranking uses. What does not pass is not kept, and what no longer passes is said to be out of date, and is never mended in silence |
| Shown again | By loading the spec into the search, as a shared search is loaded. It is ranked on the release that is served that day, and the page says so where that is not the release it was made on |
| Taken away | One search at a time, by the person. All of it with the account, in one transaction. What is taken away is gone from the file, and from what is written beside it, and not only from its tables ([0045](0045-the-service-has-a-database-one-file-for-accounts-and-what-they-keep.md)) |
| A copy | Everything Burro holds of an account, as JSON, to whoever is signed in to it |
| In a log | Nothing of any of it. No id of a search that is kept is in a line, and no spec, as before ([0011](0011-nothing-is-kept-for-a-search.md)) |

**The last searches are built two ways, and one line chooses.**

| Way | What a person meets | What it costs |
|---|---|---|
| Kept from the start | A person who signs in finds their last ten searches, having pressed nothing | Every search of a person who is signed in is written down, with the places they must reach in it, though they did not ask for that search to be kept. The privacy notice must say so where a person signs in. The regulator's guidance, as read on 2026-09-26: "Ensure any default settings offer strong privacy protections." |
| Kept once a person turns it on | Nothing of a search is kept until a person presses to keep it, or turns the last searches on in their account | A person who never finds the setting never sees their last searches. The founder asked that previous searches be stored and shown again |

Which of the two the code is left on is said in [the design](../design/accounts.md), section 7, with the line that chooses. **The choice is the founder's**, and the privacy notice is written for both.

What was weighed, and put aside:

| Way | Why not |
|---|---|
| Keep the words with the spec, so that a person sees what they typed | What is typed is never stored ([0005](0005-raw-prompts-are-never-stored.md)). The words hold what the spec does not, and an account would tie them to an address |
| Let a person name a search | A name that is typed is typed text, kept. "Near the hospice" is a name |
| Keep the ranking with the search | It would show the figures of a release that is no longer served, as if they stood. A ranking is a function of a spec and a release |
| Make the places coarse, as a share does | The search would rank otherwise than the one the person kept, and they would not know why |
| Keep a search in the storage of the browser, with no account | The website keeps nothing in the storage of a browser ([the design of the website](../design/web.md), section 10). It would be read by whoever sits at the browser next, and would not follow a person to their phone |
| Keep every search of an account, and not ten | A list of every search is a record of a person's life over months. Ten is what "shown again" needs |
| Cipher each spec under a key of the person's | With no password a person has no secret to make a key from. A key of the service's would stand in the environment of the machine that holds the file, and the standard library has no cipher for it (rule 12). The volume is ciphered by the host ([0045](0045-the-service-has-a-database-one-file-for-accounts-and-what-they-keep.md)) |

## Consequences

- **Rule 9 of `AGENTS.md` is amended.** A spec is stored in a share, and in a search that a person who has signed in chose to keep. A place id is written to a table only inside such a spec, and the name of a place only in the name of such a search.
- **A spec is stored in a second place.** Until now a share was the only one. A kept search holds the places as they were named, under an account that holds an address of email. So the file says of a named mailbox where its owner must get to each morning. It is the most that Burro holds of anybody, and [what could go wrong](../design/accounts-threats.md) begins with it.
- **A search has an id, and a route returns it**, which [0011](0011-nothing-is-kept-for-a-search.md) had ruled out. The id opens nothing by itself: a search is reached with a session, and only by the account that kept it.
- **What is typed is kept nowhere, as before.** Nothing of this record changes [0005](0005-raw-prompts-are-never-stored.md) but the one sentence that named a share as the only place a spec is stored.
- **A setting about a place of worship, kept under an account, is a fact about a person who can be named.** [The privacy notice](../legal/privacy-notice.md) read such a setting as a wish about a place, of nobody in particular. That reading is made again for a search that is kept, in its section 20, and is marked as a reading.
- **A person can ask Burro what it holds of them, and be answered.** Until now the answer was that Burro holds nothing it can tie to anybody. Of an account it can, and the copy and the deleting are built so that a person does both themselves.
- **A kept search can go out of date.** A release may drop a place or a vibe that a spec names. The search is then said to be out of date, as a share is, and is not mended.
- **A name that code makes reads as code wrote it.** A hundred searches are told apart by what each holds, in a line, and not by what a person would have called them.

## What would change it

| If | Then |
|---|---|
| The founder chooses the other way of keeping the last searches | One line, and the sentence of the privacy notice that goes with it |
| The founder wants a person to name a search | A name from a closed list of words, or a number. A name that is typed needs [0005](0005-raw-prompts-are-never-stored.md) changed first |
| A shortlist of areas is built | It holds the ids of areas and nothing of a search, as [the contract](../design/contract.md), section 11, says |
| A person wants a kept search sent to somebody else | They make a share of it, which makes its places coarse. A kept search is never opened by a link |
| The founder decides how long a kept search is kept | What is older goes, in the step that lets old tokens and old sessions go. Until then a search is kept until the person takes it away, or the account goes |
