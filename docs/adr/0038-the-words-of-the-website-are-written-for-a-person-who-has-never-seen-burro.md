# 0038. The words of the website are written for a person who has never seen Burro, and no promise is loosened for a sentence

Status: accepted, 2026-09-26. It is the founder's direction, given after they had walked through the website in a browser. [The guide to the words](../design/words.md) is its substance, and is what a person who writes a word works from. It is of the website's own words. What the service writes is not changed by it, and whether it should be is the founder's to decide: the last section says what follows then. **Amended that evening**: the words of the service were written so too, the website's words were read through as one voice, and a second walk gave the first page a heading in the founder's own words. See "Amended, 2026-09-26", below. **Amended on 2026-09-27**, once the founder had walked the website a third time: where a drawing says a thing, the words that say it again are for whoever cannot see the drawing, and one label is the founder's own, "approx data". See "Amended, 2026-09-27", below.

## Context

- The website's own words name controls and states and explain a page. They are in `apps/web/src/content/`, one file for each part. Words about a place are the service's, and the website lays them out (rule 1 of [the website's guide](../../apps/web/AGENTS.md)).
- They were written as the documents of this repository are: in short sentences, each standing by itself, in the words of the design. A page spoke of a recipe, a band, a release, a measure, a part and a share, and said what none of them is.
- The look added words of its own that day ([0033](0033-the-website-looks-like-the-map-of-a-gentle-game.md)), and [the design of the look](../design/look.md) listed them among what was open: nobody had reviewed them.
- The founder then walked through the website, and wrote what the product is to say of itself: "The overall message of the app/product is to 'Find your area' weathe rbuying, renting, or just visitin , Burro will help you find a area to call your own."
- And of its words: "Much of your copy in vibes is nonsensical, can you write copy in a manner that is more typical for a broad audience, dont default to short snappy sentances at the cost of readibilty and understanding. Dont add random summary sub heading unless it is actually additive to the user. Remember to add sentance structure like, this means, and because of that, etc".
- The website keeps its promises in words: that no place is given a verdict, that a figure is shown as it came, that what is not known is said to be not known. A sentence that reads better and says less than that has broken one.

## Decision

**Every word of the website's own that a visitor reads is written for a person who has never seen Burro, as a helpful person would say it aloud. What the words promise is as it was.**

| Matter | What is so |
|---|---|
| Who the words are for | Somebody who is choosing where to live, or where to stay. They have never seen Burro and have not read its design. They are in no hurry to be impressed: they want to understand what they are looking at, and to trust it |
| A sentence | Whole, and joined to the one before it by the words people use for that: "this means", "because of that", "so", "which is why", "for example". Being understood is chosen over being short, and no sentence is cut down to a fragment |
| A word of the product | An everyday word stands where there is one. Where a word of the product is needed, the page says what it means the first time it uses it |
| What is said first | What a thing means for the reader. How a figure was worked out is for whoever asks |
| A heading | Only where a page is long enough that a person must find their way in it. No heading sums up what follows, none stands over one sentence, and none says again what the button that opened it said |
| A label | A name. It may be short, and is clear by itself |
| The language | British English, with no exclamation mark, no sales talk and no joke at the reader's expense |
| Where it is written down | [docs/design/words.md](../design/words.md): who reads, the eight rules, six sentences as they were beside the same as they should read, and what does not change. It is written in the manner it asks for |
| What it is not of | The documents of this repository, which are for a person who changes the code. The words of the iPhone app, which are held to a copy of the website's as they stood before ([0037](0037-the-iphone-app-is-held-to-a-copy-of-the-websites-colours-and-words.md)) |

**What it never loosens.**

| Promise | What a sentence may not do |
|---|---|
| No verdict of a place | Call anything "the best", "a good area", "up and coming", "safe" or "rough". How well an area matches what was asked for is a fact of the ranking, and "the closest match" says it. "The best area" is a verdict |
| Every figure as the data gives it | Round a figure, soften it, or leave out its unit or its date (rule 6) |
| What is not known is said to be not known | Fill it in, or say it so that it reads as nought or as the middle (rule 7) |
| What the service writes is shown as it came | Say the name of a vibe, of its ends or of an area otherwise, or reword a sentence of a result. One that reads badly is said to the founder, with the words that would stand in its place |
| Made-up data says so | Take a word from the banner, which is on every page (rule 13) |
| What is said of privacy stays true | Say less than what is typed, where it goes and that it is not kept. Name a company that runs a model, or a term of one: those are the service's to say ([0019](0019-no-one-provider-and-a-key-alone-turns-nothing-on.md), [0023](0023-what-is-typed-goes-as-typed-and-people-are-told.md)) |
| When recorded crime counts is said one way | Say it another way on another page. One text says it, word for word, on every page that speaks of it ([0013](0013-vibes-are-the-centre.md)) |
| Nothing is said of what a figure of the census or of household income means | Add a word of the website's beside one ([0014](0014-evidence-first-and-census-figures-shown.md), [0028](0028-household-income-is-shown-and-never-ranked-on.md)) |

What was weighed, and put aside:

| Way | Why not |
|---|---|
| A sentence of the service written again in the website, where it reads badly | Words about a place are the service's. Written in the website, a name or a sentence could differ from what the engine holds, and no fact would stand behind it |
| A figure rounded, or a date left out, where a sentence reads better for it | A figure is shown as the data gives it. What reads badly round a figure is the words round it |
| The old sentence kept, where a test holds it word for word | The test held the sentence for a reason. It is written again to hold the reason, with the new sentence |
| A test taken out, where the new sentence fails it | Where a promise was broken the test is right, and the sentence is wrong |

## Consequences

- **The website's own words were written again**, each file with the part it belongs to. What each says now is in `apps/web/src/content/`.
- **A sentence is longer than it was, and over the answer there is little room.** Once a ranking follows a press the first result is in sight, and on a phone it is whole on the first screen, where a plain search left 16 px to spare ([0035](0035-the-search-page-is-one-box-and-the-look-gives-way-to-the-answer.md)). A line that is a line longer there costs the answer its place. What stands over the answer is said in the room there is, and measured in a browser.
- **The iPhone app says the words as they were.** Its copy of the website's words was taken before they were written again, and nothing brings it up to them.
- **The words of the service are as they were**: the meaning of a vibe, the sentence of a reason, the label of a measure, a notice. A visitor reads them beside the website's own, in another manner. *They were written again that evening: the amendment below.*
- **No test holds the manner.** That a sentence is joined to the one before it, that a word is explained where it is first used, and that a heading helps somebody find something: a person reads a change for each. *Since that evening tests hold what of it a rule can hold: the amendment below.*
- What holds what is never loosened, in `apps/web`: `test/site-copy.test.ts`, which reads every file of the website's words for the name of a place, for a word that calls a place safe or unsafe, for an exclamation mark, for the name or a term of a company that runs a model, and for the banner word for word; `test/faces.test.ts`, which fails on a character the face of a sentence lacks; `src/content/crime.test.ts`, which holds that one text says when recorded crime counts, and that it says the three ways of asking; `src/content/templates.test.ts`, which holds the sentence of a fact to the contract; `test/census/` and `test/income/`; and `figuresNotFrom`, which holds every figure of a page to a fact the service sent.

## Amended, 2026-09-26

**The words of the service were written again, that evening.** What the service writes was set beside what it would say in the manner of [the guide to the words](../design/words.md), sentence by sentence, and written so. It follows the founder's direction on the words, which asked for words a broad audience can follow. Whether each sentence stands as it was written is the founder's to say: each is one line of core.

| Matter | What is so |
|---|---|
| What was written again | Every fixed word the service writes for a person: the sentence of a figure, of a vibe, of a journey, of a cost and of what an area has no figure for; what an offer would do and what each of its ways does; a notice, a note and the message of a failure; the notes of the census and of household income; the name and the unit of a measure; what a vibe means and cannot see; and the names of two groups of the settings |
| Four words of the design that no sentence says | "In this release", "recipe", "parts" and "counted from". In their place: "the areas Burro compared", "the measurements that go into this vibe", "where the bands run from" |
| What did not move | No figure, id, rank, order, hash or count, and no recipe. No fact gained or lost a slot, and no sentence lost a figure it said |
| The versions | The engine went to 1.16.0, where it was 1.15.0, because what an explanation says changed. It is 1.17.0 since a search may be a visit ([0041](0041-a-search-may-be-a-visit.md)). The catalogue is at version 16, where it was at 15, because words of the measures and of the vibes changed, which a release carries. It is at 17 since 2026-09-27, for one line of what Quiet streets cannot see |
| What was left as it was | The names of the vibes, which are phrases a person types. Three sentences the website fills from the contract itself: two areas that are alike, and the nearest station. And the sentences that already read well, among them the caution of recorded crime, word for word |
| What holds it | `packages/core/tests/test_the_words_of_the_design.py`, which reads every fixed word of core, every word of the catalogue and every sentence of every fact of the made-up city for the four words. `services/api/tests/test_wording.py`, which reads every part of every offer and every message of a failure a person can meet |
| What it cost | The answers the website and the app are tested on were recorded again, and every test that held a sentence of the service letter for letter was brought to the new one. **The release of London that was approved was built with the catalogue at 15, and the service refuses it**, by the rule that a release and the service are of one catalogue, until London is built again with this code and its lock is committed. [The guide to data builds](../data-builds.md) says what the founder does |

**The website's own words were read as one voice.** Many hands wrote them to one guide, and none read another's, so one thing came to have several names, and a sentence that was true where it was written was untrue where it stood. `apps/web/src/content/voice.test.ts` reads every line of the website's words with its gaps filled, and holds that no line uses a word of the design, that one thing is called by one name on every page, and that a sentence which is drawn in more states than one is true of each. That a sentence reads well is still for a person to judge.

**The first page is headed in the founder's own words.** The founder walked the website a second time, and wrote: "Change describe the life you want to - tell me whats important in your space. Then give more of a discriptive explaination on what a useful sentence should be." So the box of Quick search is headed "Tell me what's important in your space", and under it a few sentences say what helps Burro most, with one whole sentence as an example ([0035](0035-the-search-page-is-one-box-and-the-look-gives-way-to-the-answer.md), as amended). It is the one place the website speaks as "me": everywhere else it says "Burro". The words are the founder's, and are kept as they wrote them.

**The same walk took words away.** What stood under the box on how words are handled, the sentences at the head of the settings, the line that says what a little town is on a list of results, and the label and the sentence of a rough guide each went. Each was true, and each was written as the guide asks. The guide says how a thing is said. Whether it is said at all, and where, is decided by walking the page: a sentence that is true and well written may still be one too many for the person in front of it.

## Amended, 2026-09-27

The founder walked the website a third time, late on 2026-09-26, and wrote of a result: "remove the explainer text under the gauges. we dont need that level of detail. just show the incomplete data icon and simple text of 'approx data'". And: "Remove the why it fits section, again too much detail". And: "Again, we don't need to over complicate and bloat with too much info."

| Matter | What was decided | What stands now |
|---|---|---|
| A drawing and the words beside it | No drawing was left to speak for itself: what each stands for was said in words beside it, in sight | Where a drawing says a thing at a glance, as a gauge says where an area sits, the words that say it again are not drawn. They are said to a screen reader, and what the drawing means is said once in the key to the drawings. The name of a thing still stands beside its drawing, in words |
| What words are for | | What no drawing can carry: a name, a figure, a source, a date, and that a thing is not known |
| "Approx data" | | The founder's own label, in their words, for a figure that is not whole. It is shorter than the guide would have a sentence be. A label is a name and may be short, and this one was chosen by the person whose website it is: it is kept as they wrote it, and nothing is written beside it |
| Where there is doubt how much to say | Nothing said which way to lean. Of one sentence, being understood was chosen over being short | Less is said, and the rest is kept one press away, whole. The founder walked the website three times, and each time kept the pictures and took words away |
| The guide | Eight rules of how to write, and five of where a thing is said | Three more of where a thing is said: not beside a drawing that says it, only what a drawing cannot carry, and less where there is doubt. And a part on "approx data" |
| What it never loosens | The eight promises of the table above | The same eight. That what is not known is said to be not known is kept on a result by the two words, and by what a result says where it has no figure at all |

What was weighed, and put aside:

| Way | Why not |
|---|---|
| What a band rests on kept beside the two words, in the service's own clause, as it stood | The founder gave the words, and asked for nothing else beside the mark |

What follows from it:

- **A result holds fewer of the website's own words than any other part of it.** Its sentences are the service's, and one is left in sight: the trade-off.
- **A visitor who does not take the meaning of a gauge has no sentence beside it to help them.** The key to the drawings says how five steps and a peg are read. It stands first on the page of vibes, which the name board of every page leads to.
- **No test holds that a sentence is needed where it stands.** It is seen by walking the page, as the founder saw it.

## What would change it

| If | Then |
|---|---|
| The founder holds that the sentences of the service are to be written so too | They are written again in `packages/core`, where the verifier holds every sentence about a place. The answers are recorded again for the website and for the app, and every test that names a sentence follows. *Done on the evening of 2026-09-26* |
| The founder chooses other names for the vibes | Each name is also a phrase a person may type. The name it had stays a phrase the reader reads, and the cases of the reader are scored again |
| A sentence over the answer stands the first result off the first screen of a phone | It is said in the room there is, and what is long is one press away. The rule that the answer comes first is not loosened for a sentence |
| The iPhone app is given the look | Its words are brought to the website's as they then stand, as [0037](0037-the-iphone-app-is-held-to-a-copy-of-the-websites-colours-and-words.md) says |
| A sentence is found that breaks a promise and passes every test | The sentence is mended, and the test that would have caught it is written first |
