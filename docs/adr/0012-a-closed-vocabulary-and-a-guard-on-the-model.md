# 0012. The reader applies a plain prompt and offers what it read of any other, and the website applies what is offered

Status: accepted, 2026-09-23. Amended the same day: the reader now applies a prompt only when the whole of it is plain, which was the next step this record named. Amended 2026-09-24: the guard on the model went, and nothing a model reads is applied. The model proposes, the person confirms, code checks. Amended again that day: what makes a limit firm, and then what is said about a thing, which the foot of this record says. Amended 2026-09-25: one press may take what a person plainly said of the home they look for, which the foot of this record says too, and later that day a journey that was plainly said, as a guide, by the rules alone as with a model, and a budget to buy a house is asked about by the kind of house. Amended again that day: a place to stay away from is never a journey to it, and a house of no kind is taken as a terraced house and said to be assumed. Amended 2026-09-26: a time in hours, an amount by the week, a journey on foot, and what is said of a home that the search cannot hold, which the foot of this record says. **Amended again on 2026-09-26, once the founder had walked the website a second time**: the website applies what was read without asking, and shows each thing as a chip that can be taken off. The rules, the guard on a model and the service are as they were, and a model still never ranks, scores or describes a place. What is given up is that nothing a model read moves a search until it is pressed. Until then this record was named "The reader applies a plain prompt and asks about any other, and a model proposes". See "The amendment of 26 September 2026", at the foot of this record, which says what that risks and what holds it. **Amended that night, once the website had been driven against the service**: where the words give no way of it, the website takes neither way of a rule that leaves areas out, nor of a thing that runs two ways, and says in a line that it left each. See "Amended that night", at the foot of this record. **Amended on 2026-09-27**: the service marks the way the words give of a wish, offers no way for more of a thing the words turn round, and says of every offer whether the words name what it counts and whether it waits for a person. The website reads both, and names no measure to keep a promise. See "The amendment of 27 September 2026", at the foot of this record. Builds on [0002](0002-deterministic-core.md) and [0005](0005-raw-prompts-are-never-stored.md). Three calls of the amendment of 24 September are for the founder to confirm, and six of the amendments of 26 September.

## Context

Burro turns a sentence into typed edits in two ways: by rules, which need no model, and by a model, whose answer is checked by code. A wish that is not read costs little, because the controls are on the screen. A wish that is read backwards costs trust: "no pubs" that puts the area with the most pubs first.

The rule-based reader was put right twice by listing the words that turn a wish round. Each time an adversary wrote a few hundred sentences and a hundred of them still came out as the opposite of what was asked. English has too many such words, and people mistype them.

The guard on the model had the same fault one step removed. It kept what a model raised unless the request held a listed sign of doubt, and it let a doubt anywhere silence the model everywhere. Thirty ways were found through it: a name put together across a bracket, "only" answered as "exclude", a hard budget nobody gave, and every sentence the list of doubt did not cover.

## Decision

**The reader.** It applies a prompt only when the whole of it is plain: a list of things wanted or not wanted, with an optional opening, a budget and a journey to a place named in full. What is plain is a grammar, written down in one place, and the words it is made of are in another. One token the grammar does not place makes the whole prompt not plain, whichever sentence it stands in, and nothing is then applied, not even a budget that was read. It is all or nothing, because no single word is ever the fault.

For a prompt that is not plain the reader offers what it noticed: each thing, place, area, budget and tenure, once, with the directions a person may choose and "Leave it out". It chooses no direction itself. It says which stretches of the text it made nothing of, as offsets. A suggestion is never logged or stored.

The grammar is wide where a wrong reading is a wrong number: a budget, a tenure, the size of a home and a journey are made of numbers, names of the release and closed lists of words. It is narrow for a wish about character, which is read only from a phrase of the lexicon.

A sentence ends only at a full stop, a question mark, an exclamation mark or a line break. A question is not plain. Every edit says which words of the text it rests on, as offsets.

Until this amendment the reader read each sentence that was made of words it knew, and left the others unread. That is what "What it still gets wrong", below, was measured on.

**The model, until 24 September 2026.** What follows under this heading was the guard. It is kept here for what it was decided on, and it no longer stands: see "The amendment of 24 September 2026", below.

It must copy, for each edit, the words of the person's that the edit rests on. The code finds those words in the text as typed, in one sentence, and asks the reader what it made of that sentence:

- In a sentence the reader knows, the reader's reading is the whole of it. A model's edit is kept only if the reader made one of the same kind there, and what is applied is the reader's.
- In a sentence the reader does not know, a model may read a wish for a thing the reader has no phrase for, and no more. It is raised only where the sentence holds no word that turns and no word of the written list of doubt, and it is marked as inferred.
- A journey, a budget and a rule about an area are the reader's alone.
- A name is the whole of a name, as typed, side by side.
- On a request about who lives somewhere, only the reader's edits are kept. A model that answers off topic does not overrule the reader.

**Where the words stand** is returned to the caller by route 1, and never logged or stored.

The contract, sections 8.2, 9.2 and 13, holds the rules in full and what each was measured to cost.

## Consequences

- The reader applies fewer plain sentences. Of 170 it applied 145 before the closed vocabulary, 142 with it, and applies 137 with the grammar. Of 60 that were held out, 55, then 46, and now 45. It offers what it does not apply.
- On the evaluation set of 738 cases it reads 375 correctly, offers 221 as suggestions, declines 137 and reads 5 in part. None is read backwards and none holds an edit nobody asked for. Every one of the 42 cases that are marked plain is read correctly, and a run fails if one is not.
- A prompt of three plain sentences about money and work is read whole, where it gave one edit of three: "I rent and can pay up to £1,500 a month for a one bed flat. I work at Cindermoor Works and want to get there within 35 minutes. A park nearby would be good."
- A long prompt is seldom plain. Of 28 very long cases none is applied, 7 are offered whole and 19 are declined. That is what a model is for.
- A model adds less than it could. With a stand-in that reads every plain sentence as it is meant, 17 of 230 plain sentences are read through a model that the reader alone does not read. They are wishes in looser words, which is what a model is for.
- A stand-in that reads backwards gets an edit applied in one of the adversary's 124 sentences, and that one is right. Held to the letter of the decision it was 52.
- The guard rests on core. It has no list of words of its own and splits no sentence itself, so a fault in core's reading is a fault in the guard.
- What still gets through is written down, and held as tests that are expected to fail: a thing in words the reader has no phrase for, turned round in words nobody listed.

## What it still gets wrong

A third adversary read the vocabulary first and wrote 725 sentences in which a person does not want a thing. 280 of them, 39%, were read as a wish for it.

What holds: "no", "not", "without", "avoid" and "less" were never read backwards in 104 tries, nor were 30 misspelt negations, nor 8 requests about who lives somewhere.

What fails is a sentence made only of known words whose meaning is against the thing, or a wish parted from its doubt by the end of a sentence:

| Sentence | What is read |
|---|---|
| Pubs are so noisy | More pubs |
| Some want pubs | More pubs |
| My street is lively and I need peace and quiet | Buzzy |
| I want pubs. Actually I do not want pubs. | More pubs |

These are sentences people will type. A closed vocabulary cannot close them, because no single word in them is the fault.

**Closed by the amendment.** None of the four is plain, so none is applied. Each is offered: pubs with more and fewer, Pace with both its ends, and the person chooses. They are cases in `evals/reader/cases/suggestions.jsonl`. The sentences the adversaries found reversed are held in `packages/core/tests/sentences.py` and in `evals/reader/cases`, and a test fails if one of them raises anything.

What the grammar cannot close is a plain list that does not mean what it says: "pubs, pubs, pubs" typed in despair. Nothing in the words says so.

## To confirm, until 24 September 2026

The three points below were of the guard that went. The amendment overtakes them, and has points of its own to confirm.

1. **In a known sentence the model adds nothing.** The decision kept a model's edit wherever the sentence held no doubt. It costs "somewhere for the kids", which a model reads as a wish for playgrounds and the reader reads as nothing.
2. **In an unknown sentence a model may not touch a thing the sentence names in the reader's own words, nor add a journey or set a budget.** The decision let it, where no doubt was listed. This is what took the stand-in from 52 to one. It costs 11 of the 230 plain sentences.
3. **An area rule is never the model's.** The decision kept one where the reader read none and no doubt was listed. It costs "cross Cindermoor off my list".

The guard on the model asked the reader what it made of each sentence. The reader still says that of each sentence alone, by `sentences_of` and `by_sentence`, though it applies a prompt whole or not at all.

## The amendment of 24 September 2026

### What was measured

One model, `gemini-3.5-flash-lite`, read 113 made-up sentences once each, as the service would ask it, on the synthetic release. Nine of them were read twice or four times more. 82 were drawn from the evaluation set, and the rest were written for the measurement before any call was made, one long natural sentence among them. The answers are kept, word for word, in `evals/reader/answers/`, all but those of one sentence that is a person's own. No test and no run of the scorer calls a provider: a stand-in hands each answer back.

| Reader | Read rightly | In part | Not read | Backwards | An edit nobody asked for |
|---|---:|---:|---:|---:|---:|
| The rules alone | 59 | 1 | 53, of which 27 were offered whole | 0 | 0 |
| The model behind the guard | 47 | 9 | 55, of which 27 were offered whole | 1 | 1 |
| The model by itself, every checked edit applied | 75 | 11 | 10 | 6 | 11 |

**The guard made the product worse than having no model.** It did worse than the rules alone on 14 sentences and better on 4, and it read one sentence backwards, which neither of the others did.

### Why the guard went

With a model on, what was applied was made of the model's edits alone, each kept only where the rules made one of the same kind in the same sentence. An edit the rules made and the model did not was not applied. So "not gritty", "near a big park" and "I work at Cindermoor Works. A 40 minute commute on foot.", which the rules read whole, came back with nothing.

The model by itself reads more, and reads some of it backwards. Five of its six backwards readings had two causes, both in the shape of its answer. It wrote `direction: less` to mean fewer stations, and for that feature `less` means a shorter walk. And a least distance, "Minimum 45 minutes from", had nowhere to go but the one field for minutes, which is a most. Sent again, five of the six were read backwards in every look. Changing the instructions would not mend them.

### Decision

**The model proposes, the person confirms, code checks. Nothing a model reads is applied by itself.**

1. **The rules read first**, and apply a plain prompt as before. Where they leave no word unread, no call is made.
2. **For any other prompt the rules make their offers, and the model is asked.** What the model says becomes offers. The two are merged, one offer for each thing. A person never sees less than the rules alone give.
3. **Nothing of a model's is applied without a press.** Not a weight, not a budget, not a notice that changes the search. This is a test and not a rate.
4. **The model says which thing, and which words. Code says the rest**: which way, how much, how firm, by what way of travelling, and whether the thing may be offered at all. Four fields of the answer are no longer read: `direction` on a thing that runs one way, `value`, `strictness` and `provenance`.
5. **Thirteen checks stand between an answer and an offer**, and a list of what is never offered from a model whatever it says. The contract, section 8.2, holds each with what it was measured to stop and to cost. Every list of words the checks use is core's. The guard writes none of its own.
6. **An offer is worded in four parts, by the API**: what it would do, the person's own words cut from the text by where they stand, what follows for areas, and the choices. Doing nothing is "Skip". What nobody said is said.
7. **A place the release does not hold is kept as a question**, with its minutes. The model is never asked where a place is, and is never sent a name of the release.
8. **"Add all" adds less than a person may**: a wish or a vibe at a mention or a small step, the tenure, a budget as a guide, a journey as a guide to a place named in full. Never what leaves areas out, what runs two ways with no guess, a journey to a place that is yet to be chosen, or recorded crime. **Overtaken on 2026-09-25 for what is said of a home**: see "What one press may take", at the foot of this record.
9. **When a model is slow, capped or broken the rules answer**, and what the rules offer never waits on a model.

What the rules offer is kept whatever a model says. For a word the rules offer what is nearest for, "safe", "a sense of community", and the words about wealth and about identity as core comes to hold them, a model's reading of the same words is dropped in favour of the rules' offer. **A vibe that counts recorded crime is never offered from a model**: typing its name asks for it, and then the rules offer it.

### What the rules reader is now

It stays, and does four things. It is the fallback. It is the judge of a plain prompt. It is where every offer begins, with every way a thing runs. And it owns every list of words the checks use.

### The floor

A model is not turned on, for any provider, until all of these hold on a measurement of that provider.

| What | No more than |
|---|---|
| A reading of a model's applied without a press | None. A test, not a rate |
| Anything offered that is never to be offered | None. A test for each row |
| A backwards reading offered with a guess marked | 1 in 100 sentences |
| A backwards reading that a model added, in any form, on sentences that are right to leave alone | 1 in 25 |
| A right reading of the rules, lost because the model was on | None. The guard that went lost 14 |

### Consequences

- On the first look of the 112 sentences whose answers are kept, the new guard offers 85 rightly, 11 in part, and makes no guess at 13. Two hold a guess at a fair reading the case does not name. One backwards reading is marked as the guess. Nothing is applied, nothing is offered that is never to be offered, and no reading of the rules is lost. `evals/reader/replay.py` counts it, and a test holds the counts.
- **That is a fit and not a measurement.** The checks were chosen after reading these answers. What they do on other sentences is not known until it is measured: on a fresh set of at least 300 sentences written by someone who has not read these answers, on each of the other three providers, with people who are shown offers, and on a release of London.
- A person must press to have anything a model read. A budget that a model read rightly eight times of eight is still an offer.
- Words put no stale search right. Where a spec names a place the release has dropped, the control that takes it out does.
- A limit that is firm in plain English and not by core's list is offered as a guide first: "can't go a penny over", "no higher".
- Two right readings of recorded crime are not offered: "no muggings", "I got burgled last year". To offer one, add the word to core, with a case first.
- The scorer judges what was offered as well as what was applied: whether to press every guess leaves the search as the case says it should be.

### What an adversary got past it

The checks were then tried with answers written to deceive: a model that is careless, or means harm, and chooses the words it quotes. Nothing was applied without a press, no answer broke the service, and no word that was typed reached a log. These got past, and were mended:

- **A firm limit nobody gave.** A quote that held "at most", said of the bedrooms or of another journey, made a budget firm. What makes a limit firm now stands against its own number.
- **An offer that rested on a wish about who lives somewhere.** A model quoted "somewhere lively", of "somewhere lively for young professionals", or "like me", of "young professionals, like me". The words are now read with their clause, and words that are no wish of their own are part of the wish beside them.
- **Recorded crime, backwards.** "I don't mind crime" and "crime doesn't bother me" were each a guess at less recorded crime, because a word that turns stood in the quote. What is said of a nuisance is now read either side of where it is named.
- **A thing the rules noticed under a turn**, rested on other words: a park on "is essential", of "I hate parks. But a station is essential". A turn is now looked for where the rules noticed the thing.
- **An end of a scale nobody named**, a way of travelling said of another thing, a thing counted above all for what was said of another, a number of one kind offered as another, and a thing rested on "a".
- **What was shown left out what the offer rested on**: "theatres? No thanks" was shown as "theatres". And the one way left of a wish in doubt was said as if it were Burro's reading.

The principle that came of it: **nothing that makes an offer stronger is read from the quote alone.** It is read where the number or the thing stands, as core finds it.

It cost the guess on three right readings of 401 by the careful stand-in, and on one budget of the answers on disk. The careless stand-in is marked backwards on 88 cases of 781, where it was 92.

### What it still gets wrong

- **A word about wealth or about identity.** Settled on 2026-09-24: core lists them, and offers two readings of the one and three of the other, all of the place. A model adds no reading of "affluent", "posh" or "a real identity", and a test holds each.
- **A turn that stands beyond a mark from the thing, or in another sentence.** "No, a park", "What I don't want: a park", "parks, no thanks". The guess is marked, and "add all" takes it.
- **Somebody else's wish.** "My mum is after a park" is offered as a wish for a park, with the guess marked, in every look. No word core lists says whose wish it is. The offer shows the clause the words stand in, so that the person can see.
- **A wish turned round in words core does not list**, of a thing the rules have no phrase for: "boozers on every corner would finish me off". A model that raises the thing there has its reading marked as the guess.
- **A request about people that both the lexicon and the model miss.**

Each but the first is held as a test that is expected to fail.

### To confirm

1. **"Max", "up to" and "under" are offered as a guide first**, with the firm limit as the second choice. "At most", "no more than" and "can't go over" are firm, by core's list. **Overtaken the same day**: see "What makes a limit firm", at the foot of this record.
2. **"Add all" never adds anything that leaves areas out.** Where the guess is a firm limit, it adds the guide, and says that the limit can be made firm. **Settled on 2026-09-25**: it adds a budget as the person worded it, and a journey as a guide still. See "What one press may take", at the foot of this record.
3. **The floor is as above.**

4. **A budget that may be a least has no guess.** It costs the guess on "I can't pay more than", which is firm in plain English and not by core's list.
5. **An end of a scale is the guess only where core's own phrase names it.** It costs the guess on "somewhere with history", where a model would read Historic rightly.
6. **The one way left of a wish in doubt is asked, and not said**, for the rules' own offers as for a model's: "More culture nearby: count it?"

Three more were made in the building, and are as easily made the other way. **A guess is held to the words that turn a wish away, and "add all" to every sign of doubt core lists.** Held to every sign of doubt, a guess was lost on "What I do want is a proper high street" and on "should be 30 to 40 minutes at most", for "what" and "should". **Where the rules and a model name different things for the same words, the guess is the rules' thing.** And **once a model has read the words, "add all" takes what Burro guesses and nothing that was only noticed.**

### What makes a limit firm

Amended on 2026-09-24. The founder typed "max £400k" and "at most 35-40min". Read as a guide, the budget ranked first an area where the middle home sold for far more. So the words that say the most a number may be are held as a limit, and a limit leaves out what is over it.

| Limit | Firm where the words against its number are | Still a guide |
|---|---|---|
| A budget | "max", "up to", "at most", "no more than", and what was firm before: "cannot go over", "absolute maximum" | "under", "below", "less than", "around", "about", "maximum", "tops", and an amount with no such word |
| A number of minutes | "at most", "max", "no more than", "within", and what was firm before: "no further than" | "up to", "under", "less than", and minutes with no such word |
| A range of minutes | Firm at its longer end, with or without a word: "35-40min" is 40 minutes and no more | The shorter end is never a limit |

The lists are core's, `FIRM_OF_MONEY` and `FIRM_OF_MINUTES`. The rules read them in a plain prompt and in an offer. The guard on a model reads them where a model called a limit firm, and the scorer of the evaluation reads them too, so the three cannot disagree. A budget or a journey that is only noticed is offered as a firm limit where the words say so, and "add all" still adds nothing that leaves areas out. Since 2026-09-25 it adds a firm budget that was plainly said, and no firm journey: see "What one press may take".

Each list was a call made for the founder, from their own sentence, and is theirs to overturn. Two things follow that they may not want. "Up to £1,700 a month" is a firm limit, and on the made-up city it leaves out sixteen of the twenty-four areas, so the example sentences of the website say "about" where they said "up to". And "maximum" and "tops" are not on the lists, so "maximum £400k" is a guide where "max £400k" is a limit.

### What is said about a thing

Amended on 2026-09-24, after the same model read the same 113 sentences a second time, through the guard as it then stood. Each was asked once, and ten of them three to five times more. The answers of the second measurement are held outside the repository, so the counts of it below cannot be made again from what is committed. Those of the first can, by `evals/reader/replay.py`, but for the founder's own sentence.

The floor did not hold. Three sentences of 113 were offered backwards with the guess marked, where it allows one in a hundred: "my mum is after a park" as the person's own wish, "a station, heaven forbid" as a wish to be nearer one, and once in four looks a deposit as a budget. The guard fitted the answers it was built from better than fresh ones: on the first answers it marked one. And a model rested Village feel on "a real identity", which is the rules' to offer.

**Decided.**

1. **A guess is never marked where the words about the thing turn the wish round, or give it to someone else.** It is read where the thing stands in the sentence, across the marks either side, and never from what a model says it quoted: the words that turn a wish are the ones a model leaves out. The thing is still offered, as a question, with the whole of the sentence shown.
2. **A guess on a scale takes the end the person named.** "Houses not flats" is Houses. An end that is turned away names the other, as the rules read it. Where a model named no end, the guess takes the end the words name only where they turned one away.
3. **A model's guess is never marked on a reading the rules keep**, whatever words it rests it on: the readings of a word about identity, about wealth, about safety. The offer is served as the rules give it with no model.
4. **The same readings make the same offers**, whatever order a model wrote its edits in.

Core lists every word: what a person dreads, thinks little of or cannot bear, who else may wish, the third person of a wish, and the ends of a scale that a word for a home names. None is a word of the grammar, and the rules read as they did.

**What it did**, on the first look of each sentence. "Before" is the guard as it stood on this branch, after core came to list the words about wealth and identity, which is why it reads 81 of the second measurement rightly where the measurement itself counted 82.

| | The first answers, before | after | The second answers, before | after |
|---|---:|---:|---:|---:|
| Sentences | 113 | 113 | 113 | 113 |
| Read rightly | 84 | 85 | 81 | 82 |
| Offered backwards, with the guess marked | 1 | 0 | 3 | 1 |
| Offered backwards by a way a model added, with no guess | 0 | 0 | 1 | 1 |
| Applied without a press | 0 | 0 | 0 | 0 |

A fifth of the sentences, 23, was held back by a hash of each id before any answer was looked at, and scored once the checks were written. All three sentences that were offered backwards fell in it. The report of the measurement had named them, so it was no blind test of those three. On it the guard marked a backwards guess on 3 of 23 of the second answers before and 1 after, and read 12 rightly before and 13 after.

**One in a hundred holds on these answers, with nothing to spare**: 1 of 113 is 0.9 in 100, and a second would break it. It is still a fit and not a measurement.

**What it cost.** With a stand-in that reads every case of the evaluation set rightly, 399 of 820 cases are right where 401 were. Three lost their guess, each a wish of somebody of the speaker's own: "My husband wants a pub nearby and I want a park", "My wife says parks, and what she says goes", "I'm asking for my brother: he wants pubs and a station". The cases say a careful person would raise each. The guard asks. One gained it: "To be avoided at all costs: nightlife". With a stand-in that raises whatever is named, 73 are marked backwards where 89 were.

### What it still gets wrong, after the second measurement

- **A number that is no budget.** "I have a 50k deposit" was a budget of £50,000, with the guess marked, in one look of four. Core lists no word for what an amount is of but money, minutes and bedrooms.
- **A turn in another sentence, in the heading of a list, or in words core does not list.** "A park? No thanks.", "Dealbreakers: pubs", "a station would drive me up the wall". They are most of the 73. *Since 2026-09-27 a turn in another sentence or in the heading of a list is read, of a thing the rules noticed, and not of a thing only a model read. A turn in words core does not list is not.*
- **A way a model adds to a question.** "Everyone tells me to live near the station but the trains would drive me mad": in one look of four the model added more lines nearby, and it stands as a third way of the rules' question, with no guess.
- **What a model reads differs from one asking to the next.** Of ten sentences asked four to six times, five came back one way and five did not, before and after. The founder's sentence came back three ways in six looks: with a guess at culture, without one, and once with the notice about who lives somewhere and no journey. The order of a model's edits no longer changes what is offered. What it reads, which words it quotes and whether it flags a sentence still do, and code cannot make those the same.
- **The rules' question about a place is dropped where a model reads.** The rules alone ask which place "Chancery lane" is. With a model on, the question is asked only where the model reads the journey too. The scorer counts it as a reading of the rules lost, on the founder's sentence and on two cases like it. It was so before this amendment, and is not mended by it.

### To confirm, of what is said about a thing

1. **A wish of a partner's is asked, and not guessed.** The evaluation set says two people make one search. Either the cases change or the guard does.
2. **A word for a home alone names no end.** "A flat" stays a question, and "houses not flats" is Houses.
3. **Where a model names no end of a scale, the guess takes the end the words name only where they turned one away.** Let through for every end that is only named, a stand-in that raises whatever is named was marked backwards on eleven cases more.

### What one press may take

Amended on 2026-09-25. The founder typed their own sentence into a browser: a quiet place with parks, a journey from Chancery Lane, and "If I'm buying, max £400k for a 1 bed flat". Thirteen things were offered. With a model reading, three carried Burro's guess: quiet streets, a park and the journey. The one button took those three. Buying, a budget of £400,000 and a flat carried no guess, though the person plainly said each. After the press the search still assumed renting and held no budget, and the first results were flats the person could not buy at their price. The answer took ten presses.

**Decided by the founder: one press may take what a person plainly said: that they are buying, their budget, and the kind of home.**

1. **What is plainly said of a home carries Burro's guess**, whether or not a model reads: that a person is renting or buying, a budget with its amount, and a kind of home.
2. **One press takes each**, with the rest that need no choice. **A budget is taken as the person worded it**: firm where they used a word of `FIRM_OF_MONEY`, "max", "up to", and a guide where they used none. A kind of home is taken with its note, which says what Burro cannot hold of what was said, and is shown before the press.
3. **A journey is taken as a guide, and never as a firm limit.** A journey is estimated from distance and no timetable stands behind it ([0027](0027-a-journey-is-estimated-from-distance-until-a-timetable-is-held.md)), so one press must not leave areas out on an estimate. On the first build of London, which is a preview, a firm limit of 40 minutes to Chancery Lane leaves out 422 of 1,002 areas. A person makes a journey firm with a press of its own. **Settled later on 2026-09-25: it is so by the rules alone too.** That the journey stays as it is was said of this rule, and not of what the rules offer. See "A journey by the rules alone", below.
4. **The rules that stay.** One press never takes recorded crime, anything that counts who lives somewhere, anything offered as a question, or a reading the rules keep for themselves, such as the readings of "affluent" and of "a real identity".

### What plainly is

The decision was to hold it to what the rules already mean by no doubt: the words stand in the sentence, nothing beside them turns them round or gives them to someone else, and the amount is one amount. Held to that and no more, six of the 901 sentences that are held as cases were a backwards guess: "I earn 60k" and "I have a 50k deposit" as a budget, "I'm done renting", "Renting is dead money" and "Finally escaping the rental market" as renting, and "Buying is out of the question" as buying. Two of the six are among the 112 answers on disk, where the floor allows one. So it is held to more, and every part is asked of what the rules read.

| What is asked | How it is kept |
|---|---|
| The rules would apply the clause, were it all that was typed | The clause the words stand in, from one mark to the next, is read by the rules alone. They apply a prompt only where the grammar makes the whole of it. "Max £400k for a 1 bed flat" is such a clause. "I earn 60k" is not, for "earn", and nor is "I'm done renting", for "done". So one press takes no more than Burro does unasked of a plain prompt |
| An "if" that leads the clause in is no doubt | "If I'm buying" says which of renting and buying the rest is said of, and is read as "I'm buying". Core lists the word, as `IN_CASE`. It is still no word of the grammar: a prompt that holds it is not plain, and nothing of it is applied. "Buying if I must" and "if I could buy" hold doubt that core lists |
| The words give one of each | One tenure, one amount, one kind of home. "If I rent, up to £1,700 a month, and if I buy, max £400k" sets one case against another: it names both tenures, and nothing of it is the guess. Two amounts leave the tenure and the home plain, and two kinds of home leave the rest plain |
| The wish is nobody else's | It is read where the amount stands, or the word for the tenure or the home, as far back as the start of its sentence and no further than "but" or a wish of the speaker's own: "my partner wants to buy" |
| Nothing beside it puts it in doubt | No sign of doubt that core lists stands in its clause, and its sentence does not ask |

Whose wish it is and which tenure is meant are asked of a model's reading of a budget too. Where either is in doubt no guess stands on what is said of a home, whoever read it. `plainly_said` in `guard.py` holds all of it, and `in_add_all` in `offers.py` what one press takes.

### What it did

- **The founder's sentence, on the first build of London.** By the rules alone one press takes five of the thirteen: quiet streets, culture nearby, buying, the budget and the flat. It takes six since later that day, the journey among them: see "A journey by the rules alone". With a model that reads quiet, the park and the journey it takes six: those three, and buying, the budget and the flat. The search then holds a home to buy, a flat, and £400,000 as a firm limit. 771 areas are ranked and 231 are left out, each where the middle price of a flat is more than 25% over the budget. On the made-up city the same sentence leaves out 16 of 24.
- **"My partner wants to buy but I'd rather rent, max £400k".** One press takes nothing, by the rules alone and whatever a model answers. All of it is offered, each by its own button.
- **What the rules mark, pressed.** Of the 901 sentences, 41 hold a guess of the rules. To press every one leaves 2 right and 38 in part, and one where nothing that was asked for was guessed. None is backwards and none holds an edit nobody asked for. A test holds it: `test_to_press_every_guess_of_the_rules_does_the_opposite_of_no_case_that_is_held`.
- **What holding it to the clause cost.** Held to the words alone, 70 of the 901 held a guess, and to press every one left 10 right, 49 in part, 6 backwards and 2 with an edit nobody asked for. Held to the clause, 29 fewer hold a guess and 8 fewer are right: "I'm a buyer, £325,000, semi-detached ideally" takes buying and the budget and leaves the kind of home, for "ideally".
- **The answers on disk are as they were**: 84 right, and no backwards reading marked as the guess. `test_replay.py` holds the counts.
- **By the rules alone one press takes less of a home than it did.** It took a tenure, and a budget that was no firm limit, wherever the clause held no sign of doubt. So "I'm done renting" set renting at one press, and "I have a 50k deposit" a budget of £50,000. Neither is taken now.
- **A firm budget leaves areas out at one press.** The line after the press says how many, and "Take it all back" puts the search back as it stood.

### What it still gets wrong, of what one press takes

- **By the rules alone the journey is not taken.** The rules offer a journey one way, as it was worded, and "at most 35-40min" is a firm limit. One press takes no firm journey, and the rules make no guide to take in its place. With a model it is offered both ways, and the guide is taken. To take it by the rules alone, the rules would offer a journey both ways. **Mended later on 2026-09-25**: see "A journey by the rules alone".
- **A deposit in a clause of its own.** "I have a decent deposit, around £50k" is a budget of £50,000, with the guess: "around £50k" is a clause the rules apply. Core lists no word for what an amount is of but money, minutes and bedrooms.
- **What is plainly said in a clause that holds a word the grammar does not place.** "We're hoping to buy a flat for around £350k" carries no guess of the rules', for "hoping". With a model on, its reading of the budget is the guess.
- **A kind of home in a sentence of its own, in a search of the other tenure.** Of "Honestly. Buying. Max £400k. A flat." one press takes buying and the budget, and leaves the flat: read alone into a search for a home to rent, "a flat" is no kind of home Burro holds.

### To confirm, of what one press takes

1. **Plainly is what the rules would apply of the clause alone.** It is narrower than the words of the decision, and was made so to hold the floor.
2. **Where the words name both tenures, nothing of a home is taken**, not even an amount that can be of one tenure alone.
3. **"If" is the one word that leads a clause in.** "When I'm buying" and "as I'm buying" carry no guess at buying.
4. **By the rules alone the journey waits for a press of its own.** **Settled later on 2026-09-25**: it does not. One press takes it as a guide.

### A journey by the rules alone

Amended later on 2026-09-25. No model is turned on where Burro is hosted, so what the rules alone give is what a person gets. Of the founder's sentence they gave a journey of at most 40 minutes to Chancery Lane one way, as a firm limit. No press takes a firm journey with others, so one press took nothing of it, and it waited behind "Show all 13".

**Settled: where the rules read, with no doubt, a journey to one place with one time, the offer carries the guess and is offered both ways, and one press takes it as a guide.** A person makes it firm with a press of its own. It is offered exactly as a model's reading of it is.

| What is asked | How it is kept |
|---|---|
| One place | The rules offer the journey one way, to a place the release holds. A journey to a place that is yet to be chosen is asked about, and carries no guess |
| One time | The offer holds a number of minutes. In the sentence it stands in, no other number may be one of minutes, but for the other end of its own range. Of "30-45 minutes, no more than 40" and "at most 30 minutes, ideally 20" which is meant is the person's to say. A journey with no time has no limit to be firm, and is offered as it was |
| The rules would apply the clause, were it all that was typed | As for a home. "At most 35-40min commute from Chancery Lane" is such a clause. "I commute from Chancery Lane" is not: the place may be where the person lives now. Nor is "max 30 minutes to one place or another", nor "within 40 minutes by car", which is a way of travelling Burro does not hold |
| What is offered is what the rules would apply | The place, the minutes and the way of travelling are those of the clause read alone, so "by bike" is kept. The guess is on the way the words give: the firm limit where a word of `FIRM_OF_MINUTES` stands against the number, "at most", "within", "max", and the guide where none does |
| A range is read as the rules read it | Of "35-40min" the longer is taken, 40, and a range is a limit at its longer end with no word against it: whoever gives one has said how long is too long. The offer says which was taken, in its note, and is taken with its note |
| Nothing beside it puts it in doubt | No sign of doubt that core lists stands in its clause, and its sentence does not ask: "is 30 minutes too far?" |

A journey is nobody's wish, so whose it is is not asked: a partner's workplace is a place the household must reach. `_journey_as_said` in `guard.py` holds it.

**What it did.**

- **The founder's sentence, on the first build of London, by the rules alone.** One press takes six of the thirteen: quiet streets, culture nearby, the journey to Chancery Lane as a guide of 40 minutes by public transport, buying, the budget and the flat. The journey is in sight before "Show all". 771 areas are ranked and 231 are left out, each over the budget, and none for the journey.
- **What the rules mark, pressed.** Of the 901 sentences, 42 hold a guess of the rules, and five of them a guess at a journey. To press every one leaves 2 right and 39 in part, and one where nothing that was asked for was guessed. None is backwards. The scorer presses the guess, which for a journey may be the firm limit. One press takes the guide of each of the five.
- **The answers on disk are as they were.**

**What it still gets wrong.**

- **A journey with no time is taken as it was**, and the rules read a place after words that do not say a journey to it. Of "my ex lives at Pellam Exchange, 30 minutes away at least" they offer a journey to Pellam Exchange with no time, and one press takes it. It was so before this amendment.
- **A journey in a sentence that holds another time is not taken.** Of "at most 40 minutes to Pellam Exchange and a park within 10 minutes' walk" the journey waits for a press of its own.
- **Minutes that stand apart from the place are lost.** Of "my partner works at Pellam Infirmary, 30 minutes max" the rules offer the journey with no time.

### A place to stay away from

Amended later on 2026-09-25. In a prompt that is not plain the rules offer any place that is named as a journey to it, one way. While one press took no journey by the rules alone that cost little. Once it took one, "my ex lives at Pellam Exchange, 30 minutes away at least" added a journey to that place at one press. **A person who asked to live far from somebody was ranked by how near they were to them.** It is the worst misreading Burro can make of a place, and it is of a person's safety.

**Decided: a journey that is read backwards is never taken by one press.**

1. **A place that is named with a word for staying away carries no guess, is taken by no press, and is never applied from a plain prompt.** By a word for far, wherever it stands in the sentence of the place, and by a least against a number of minutes. The rules offer it with nothing to choose, and say why in one sentence: "Burro cannot rank on being far from a place."
2. **A place that may be somebody else's is offered, and no press takes it with others.** Where the words do not say that the person or their household must reach it, Burro does not guess.
3. **"My partner works at" and "my kids' school is" are places a household must reach**, and are read as they were.
4. **A model's reading is held to what the rules say of the place.** Of a place to stay away from it is dropped. Of a place that may be somebody else's it is no guess.

**How the two are told apart.** By who is named before the place, in its clause, and by whether a word says that they live there. Each is a closed list in core, `vocabulary.py`.

| The words | Who | What is made of the place |
|---|---|---|
| "I work at", "my boss and I work at" | the speaker's own words for a journey | a place to reach |
| "my partner works at", "and my partner at" | one of the household, `OF_THE_HOUSEHOLD` | a place the household must reach |
| "my kids' school is" | nobody that `SOMEBODY_ELSE` names | read as it was |
| "my partner lives at" | one of the household, with a word of `LIVES_THERE` | offered, and not taken |
| "my ex lives at", "my mate works at", "his mother is in", "she's at" | somebody else, `SOMEBODY_ELSE` | offered, and not taken |
| "we moved from" | a place that was left, `LEFT_BEHIND` | offered, and not taken |

Where the words do not say, the place is offered and nothing is guessed. "She" and "he" are nobody the words name, so where a partner was named a sentence before, "she's at" is offered and not taken.

**What was read from core before a word was added.** Core already listed every word for far and for a least as one that turns a wish away or puts it in doubt, and read them only before the name of a place, in its clause. `STAYS_AWAY` and `AT_LEAST` name the ones that are said of a place, and are read through the whole of its sentence. New to core are "over", "or more", "a minimum of", "not less than", "upwards of" and "at the least" as a least, "nowhere near" as a phrase, the household, who "his", "her" and "their" are, and what says that somebody lives somewhere.

**What it did.**

- **The sentence that was found, and twenty-one more**, on the made-up city and on the first build of London, by the rules alone, with a made-up model that reads every place as a firm journey to it, and with a model that fails: no journey is applied, none carries a guess, and one press takes none. Sixteen are answered with nothing to press, and six are offered by a button of their own.
- **What the rules mark, pressed, is as it was**: of the 901 sentences 42 hold a guess, 2 are right, 39 in part, one is not read, and none is backwards.
- **The answers on disk are as they were**: 84 right, and none backwards.
- **Every count of the scorer is as it was but one.** "Offered where nothing was asked" is 146 where it was 141: five sentences that ask for a least distance are now answered with the sentence, which the scorer counts as an offer though nothing of it can be pressed.
- **Seven cases of the evaluation set are read anew**, and each as its case asks: five that give a least distance are said to be so, and "my ex works at" and "my mate works at, not me" are offered with no press.

**What it still gets wrong.**

- **A wish to stay away that core's words for dread say, and no word for far.** "I hate Pellam Exchange" and "I don't want to be near Foxholt Works" are offered nothing, as before, and are told nothing of why.
- **A word for far that is said of another thing.** Of "at most 40 minutes to Pellam Exchange, and far from the motorway" no journey is offered. The person adds it with the settings.
- **A place of a partner who was named a sentence before.** "She's at" is offered, and no press takes it.
- **A place that is misspelt is no place the rules read**, so nothing is said of it.

### A budget for a house

Amended later on 2026-09-25. "Buying a house, about £600k, near a station" is a plain prompt, and was applied whole. A search to buy holds a flat until a kind of home is said, and "a house" said none, so the budget was held against what flats sold for.

**Decided: a house is never held against what flats sold for.** Where a person names a house, the budget is held against what houses sold for where the release carries that, and where it does not the answer says so.

**What a release carries.** A price is held by the kind of home: a flat, a terraced house, a semi-detached house, a detached house. No release holds a figure for a house of any kind, and the contract has no kind of home to hold one under.

| Release | Areas | Flat | Terraced | Semi-detached | Detached | A house of any kind |
|---|---|---|---|---|---|---|
| The made-up city | 24 | 21 | 21 | 21 | 19 | none |
| The first build of London, a preview | 1,002 | 984 | 940 | 653 | 282 | none |

So what houses sold for is carried, by kind, and which kind a person means is theirs to say. It matters which: in the first build of London a terraced house sold for more than a flat in 918 of the 922 areas that hold a price for both. A flat is within £600,000 in 879 areas, a terraced house in 461, a semi-detached house in 276 and a detached house in 34.

**Decided the same day, by the founder's own decision of that morning: a house of no kind is taken as a terraced house, and the kind is said to be assumed.** That morning it was decided that one press may take what a person plainly said of a home, because the answer was too many presses away. To ask which kind of house costs three presses where there were none, and goes against that. So the question is kept only where a terraced house cannot serve.

**It is a default, and the founder may overturn it.** It is `DEFAULT_HOUSE` in `burro_core.spec`, and one line. To ask which kind was built first, in the two commits "Ask which kind of house a budget to buy a house is for" and "Record the answer to a budget for a house, and hold the clients to it", and is one commit away: `_for_a_house_of_no_kind` makes the prompt not plain again, and the offer loses its guess.

1. **Where a person plainly names a house and no kind of house, the budget is held against what terraced houses sold for.** A plain prompt is applied whole, with no press, and the answer says that the kind is assumed, `Assumption.code` `segment`, as it says of public transport where a person named no way of travelling.
2. **In a prompt that is not plain, the budget is offered for a terraced house first, which carries the guess and which one press takes**, as it takes any home that was plainly said. Semi-detached and detached are each a way of the same offer, one press away.
3. **The offer says why, in one sentence**, of the release that is served: "You named no kind of house, so Burro has taken a terraced house, the least dear kind in most areas. Semi-detached and detached are one press away." That it is the least dear kind is said only where it is, in more than half of the areas that hold a price for any kind of house. In the first build of London it is, in 884 of 953.
4. **The kind stands in an edit of its own, which says whose it is.** The one Burro took is `inferred`, and a client marks the kind as assumed after the press. One that a person presses is theirs.
5. **An area that holds no price for a terraced house has no figure for that budget, and is held to the price of no other kind.** It is ranked, it is not left out by a firm limit, and it says that the limit could not be tested. The first build of London has 62 such areas of 1,002.
6. **Where a release holds no price for a terraced house, which kind it is is asked**, of the kinds that have one, as it was built first. Where it holds a price for no kind of house, the budget is said to be missing, as any figure that is not in the data is.
7. **A model's reading of the amount is dropped.** It rests on words the rules offer with a note, which are the rules' to offer.
8. **Nothing else of a home is read another way.** A kind that is named is the kind. A rent is held by the number of bedrooms, whatever kind of home it is for. A house with no amount holds a budget against nothing.

**What it did.**

- **The floor of core's plain sentences is back where it stood**: of 170 the rules apply 136. "A house to buy for about 500k" is applied, held against a terraced house.
- **The evaluation set is as it was**: every count of the scorer, and of the answers on disk. Of the 901 sentences, what the rules mark is right or in part in each that holds a guess, and none is backwards.
- **On the first build of London, by the rules alone.** "Buying a house, about £600k, near a station" is applied with no press: to buy, £600,000 against a terraced house, flexible, nearer a station. 970 areas are ranked and none is left out. Of whole-003, "Two bed house, max £650k", one press takes £650,000 against a terraced house as a firm limit: 721 areas are ranked and 281 are left out as over the budget.

**What it cost.**

- **A person who meant a semi-detached or a detached house is shown a search they did not ask for**, until they read the word "assumed" or the note. In the first build of London a terraced house is within £600,000 in 461 areas, a semi-detached house in 276 and a detached house in 34.
- **In the row of chips a kind of house that was assumed is always named.** A part that nobody said is folded into "rest assumed" where there are two. A kind of house is not: it is what the budget is held against.

**What was not chosen.**

- **A figure for a house of any kind.** The sales of the three kinds would be read together by the build. `Segment` would gain a kind, which is a change to the contract and to every client.

**What it still gets wrong.**

- **A house that is named of another home is heard as the home that is looked for.** Of "selling the house, buying, max £500k" the budget is asked about by kind of house.
- **The number of bedrooms of a house to buy is heard and not held.** Of "two bed house, max £650k" the budget is held against what terraced houses of any size sold for, and the two bedrooms are said not to be in the data.

### A time in hours, an amount by the week, a walk, and what a home cannot hold

Amended on 2026-09-26. Four things a person types every day were read wrongly, and each was found by typing it. Of "1 hour 15 to Cindermoor Works" the rules offered a journey of 15 minutes, which one press took. Of "£350 a week" they offered a budget of £350, which the search holds by the month. "Walking distance to Cindermoor Works" was applied as 45 minutes by public transport. And "buying a 3 bed house up to 600k" was applied with its three bedrooms in no list: not applied, not offered, and not said to be unread.

**Decided.**

| What is typed | What is made of it |
|---|---|
| A time in hours | It is a number of minutes, read where a number is read: "1 hour 15" is 75, "1h" 60, "an hour and a half" 90, "three quarters of an hour" 45. Minutes that stand after hours with no word of their own are read from 5 to 59. Hours typed with a point are read only as a half or a quarter of an hour: "1.30 hours" is an hour and a half as a clock shows it, and is not read. No word for hours is a word of the grammar: `hours_at` in core's `reading.py` reads them |
| The minutes of a longer time | They are never offered by themselves. A time is not put together across a mark, so "1 hour, 15 minutes to" is no time that was taken, and 15 is offered nowhere. `part_of_a_longer_time` in `grammar.py` holds it |
| A time that stands before a place and was not taken | No journey is offered at the usual 45 minutes. The place is said to be heard, with nothing to choose, and its note says why: "Burro could not take the time beside this place as the time of a journey. Say the whole of it in minutes." |
| An amount by the week | It is offered as what it comes to by the month, at 52 weeks to 12 months, to the nearest pound: "£350 a week" is £1,517 a month. The note says that it was worked out, and from what. It is never applied: a prompt that holds one is not plain. It carries no guess, so one press takes none of it |
| An amount by any other period | A year, a fortnight, a night, six months: it is not read, and its words are said to be unread. Nobody can say what it comes to by the month. So with a word for a period that stands beside an amount in any way the lists do not hold |
| Words for near that say a walk | "Walking distance to", "a short walk to": the journey is one on foot. Where no minutes are said it is held at the usual 45, which is said to be assumed |
| A way of travelling beside a place | It is taken where it stands before the name, between the time and the name, or straight after the name, and nothing more is said of it: "a 25 minute walk to", "30 minutes to Pellam Cross by bike". A way that what follows denies, that somebody else goes, or that a word turns, is not read. Of two ways said of one journey neither is taken |
| What a home cannot hold | The bedrooms of a home to buy, the kind of house of a home to rent, a studio or a room to buy. A plain prompt is applied as it was, and each is said as a suggestion with nothing to choose but to skip, in the words the offer of a home says it in. Nothing of it is unread, so no model is asked, and the status of the answer is as it was |
| Two sizes, or two kinds, of home | The prompt is not plain: nothing is applied, and each is offered. A flat and a house to buy are two kinds. The first of the two was applied, and the second was in no list |
| A model's reading of any of them | It is held to what the rules say. A reading of "£350 a week" as £350, or of "1 hour, 15 minutes" as 15, is dropped as a number the person did not type |

The contract, section 8, has each with the words it is read by.

**What it did.**

- **The evaluation set holds 911 cases, where it held 878**: 481 are read rightly, 291 are offered, 4 are read in part and 135 are declined. None is read backwards and none holds an edit nobody asked for. All 92 plain cases are applied. The share read rightly is 0.528 over a floor of 0.52.
- **Four cases are read better and none worse.** Thirty-three were added, each at the end of its file.
- **The engine is 1.15.0, as it was.** The reading changed, and neither the ranking nor a rule of the reducer did. No recorded answer of the website changed, and `contracts/openapi.json` is as it was.
- **The vocabulary is smaller.** Five phrases for hours left it. It holds 572 words and the known words are 306, and the two bounds came down with them.
- **Then 3,258 sentences were typed against it, to find a wrong reading.** Thirty-three kinds of wrong reading were found, thirteen of them new with the change and twenty older than it. Twenty-two were mended, and eleven were left.

**What it still gets wrong.** Each was found and left. Most are older than this amendment.

- **Minutes that stand apart from their place are lost, and one press adds 45.** "30 minutes max by bike to Cindermoor Works", "about 30 minutes or so to". An hour with a word after it is answered with the note, and minutes are not.
- **A journey that what follows turns is offered and taken**: "an hour to Cindermoor Works is out of the question". It is taken at 60 minutes, where it was taken at the usual 45.
- **A journey to a place that is somebody else's is offered and taken**, where the words are none that core lists: "my stalker works at".
- **Any number straight before "to" and a place is read as minutes**: "I take the 25 to", "trains every 15 minutes to".
- **An amount by the week that is turned, a least, a wage or one person's share** is offered as a budget, by its own press: "£350 a week is too much", "I earn £700 a week".
- **A house or a flat to rent with no bedrooms, and a house to buy with no amount**, are applied, and the kind of home is in no list. Two tests hold that such a prompt carries no suggestion, which is a rule.
- **A time that a mark parts is lost, where the older reading was the likelier**: of "half an hour, 40 minutes to" nothing is taken, where 40 was offered.
- **Behind a model, a plain sentence that leaves one word unread is applied by nobody.** The service asks the model wherever the rules left words unread, and then returns no edits: of "leafy, a flat", typed by a renter, the wish for leafy is lost. It is a fault of the service and not of the reading, it is older than this amendment, and a model is on where Burro is hosted. *Mended on 2026-09-27: a prompt that the rules applied is handed to no model, though a word of it is unread.*

**To confirm.**

1. **A week is worked out at 52 weeks to 12 months.** `by_the_month` in core's `interpret.py` is the one place the rate is written.
2. **A walk with no number is held at the usual 45 minutes.** A shorter usual time for a walk may be wanted.
3. **What a home cannot hold is said as a suggestion with nothing to add.** The website draws it under "Choose what to add", which reads oddly over it.
4. **Two sizes make a prompt not plain.** "I can pay up to £1,300 for a studio or a one bed" was applied with the one bed. Now nothing is applied and each is offered, and no offer of that clause carries a guess, the budget included. To apply the rest and offer the two would be kinder, and needs a state the contract does not have.
5. **The case `other-027`**, "within half an hour of them", expects no firm limit, where every other case with "within" expects one. Now that the time is read, the case is the founder's to amend.

## The amendment of 26 September 2026

The founder walked the website a second time, and wrote: "When running a search, don't ask the user to add anything, assume they want it to be added and just present the results. Is this due this demo not having gemini?"

**It was not for want of a model.** Asking was the rule of this record, whoever read. The rules applied a prompt only where the whole of it was plain, and offered what they noticed of any other. What a model read was offered too, and nothing of it was applied without a press. So the page asked with a model on as it asked with none.

The day before, the founder had typed a sentence of their own, and the answer took ten presses. One press was then let take what was plainly said. Walked again, the page still asked before it answered, and a person who has typed what they want is waiting for areas, and not for a question.

### Decision

**The website applies what was read, ranks, and shows the results. It asks nothing. Each thing it applied is a chip in what Burro understood, which can be taken off, and one that nobody said in so many words says "assumed".**

| Matter | What stood | What stands now |
|---|---|---|
| The rules read first | They read every prompt, and a model is asked only of what they left unread | The same |
| A plain prompt | The service applies the whole of it | The same |
| Any other prompt | The service applies nothing. It returns what was noticed as offers, each with its ways, with Burro's guess marked on one of them where it has one, and with the way that one press may take | The same. **The service is not changed**, and no route, record or rule of the contract moved for this |
| What the website does with an offer | It drew the offer under "Choose what to add", in four parts, and sent nothing of it until a person pressed | It sends the edits of one way of the offer, as the service gave them, with those of every other offer of the answer, and ranks. No offer is drawn, no button adds several things, and no dialogue asks |
| Which way of an offer is sent | The one a person pressed | The table below |
| The guard on a model | Thirteen checks stand between what a model answers and an offer, and some things are never offered from a model whatever it says | The same. It is the service's, and what it turns away never reaches the website |
| What is said of what was applied | The line after a press said what was added, and what was left for the person | The line under the box says what happened, as it does of a plain prompt. Each thing is a chip, in the words the chip of that thing has. What nobody said in so many words says "assumed": a way that was Burro's guess, a way that was taken as the gentler, and every part of a thing that the words did not give |
| What could not be read | Said in a line, with the way to see it in the box | The same. It is no question |
| A model never ranks, scores or describes a place | [0002](0002-deterministic-core.md) | The same. A model is asked what a sentence says, and nothing of any place |

**Which way of an offer the website takes.** It builds no edit of its own: every edit it sends is one the service gave with a way of the offer, unchanged but for the place of a journey that held none. It chooses among the ways, in this order, and `apps/web/src/lib/search/takes.ts` is the one place that does.

| # | The offer | The way that is taken | Why |
|---|---|---|---|
| 1 | The service names the way that one press may take, in `add_all` | That way, as the one press took it: a wish or a vibe at a mention, that a person rents or buys, a kind of home, a budget as the person worded it, and a journey as a guide | It is what the founder decided on 2026-09-25 that one press may take, with every rule of "What one press may take", above |
| 2 | It names none, and the offer is of a limit that may be firm or a guide | The guide, whichever the words give | No area is left out on a guess. A budget that was plainly said with a word that makes it firm is named by the service, in the row above, and is firm as it was at one press |
| 3 | It names none, and marks one way as Burro's guess | The way that is the guess | The guess is on the way the words give, where no check of the guard fired |
| 4 | A thing that runs two ways, more or fewer, or towards either end of a scale, with no guess | More of what the name of the thing says, for that evening. **Since that night neither way is taken**, and the thing is said to be left: "Amended that night", below. A thing that runs one way is taken that way, as it was | It is the gentler of the two: it leaves no area out. It is also what this record was written against: see what it risks, below. That nothing is taken of such a thing, and a line says that Burro could not tell which was meant, is built too, and `WHERE_BURRO_CANNOT_TELL` in that file chooses |
| 5 | A name that several places bear | The first of them the service gives | The service gives them in its own order, and the chip names the place that was taken, and says that it was assumed |

To skip a thing and to stop counting it are no ways of taking it, and are never chosen.

**What is never taken.** One line under the box, over what Burro understood, says what was left out. It asks nothing, and what it names can be added under "Refine search".

| Never taken | Why |
|---|---|
| Recorded crime, in any form: a measure of it, or a vibe whose recipe holds it | Recorded crime counts only when a person asks for it by name ([0006](0006-rank-places-not-residents.md), [0013](0013-vibes-are-the-centre.md)). A word that was offered as recorded crime, as "safe" and "posh" are, is no name of it |
| A vibe or a measure that counts who lived somewhere | Of residents, only their age and the make-up of their households may be ranked on, and only where a person asks for more of what a figure counts (rule 8 of [the guide](../../AGENTS.md)). The rules offer such a thing and never apply it |
| A journey to a place Burro does not know, where the data holds none with a name like it | There is no place to take |
| Since that night, where the words give no way of it: a rule for an area, which looks only there or leaves it out | Either leaves areas out, and no area is left out on a guess. "Amended that night", below |
| Since that night, where the words give no way of it: a thing that runs two ways | More of it may be the wrong way round. "Amended that night", below |
| What the service offers with nothing to choose but to leave it out: a place to stay away from, what a home cannot hold | There is nothing to take. What the service says of it is said |

**This is the one exception to what the founder asked, and it was made for them.** The founder asked that Burro ask nothing, and assume that a person wants everything it read to be added. Everything is added but recorded crime and what counts who lives somewhere, because a promise of the product forbids those two: neither counts until a person has asked for it. Nothing is asked of them either. They are left out, and said to be. It is the founder's to overturn, and to overturn it is to change the rule on recorded crime and rule 8, which is a decision of its own and a change to [0006](0006-rank-places-not-residents.md). Since that night two kinds of thing more are left, and for another reason: no promise forbids them, and each is taken wherever the words give its way. They are left where the words give none, because a guess at either costs a person more than the wish that waits.

### What it gives up

The amendment of 24 September 2026 decided: "Nothing of a model's is applied without a press. Not a weight, not a budget, not a notice that changes the search. This is a test and not a rate." It was the first row of the floor that a model is held to before it is turned on. **It is given up, of the website.** A reading of a model's now moves a search as soon as it is in, and so does a reading of the rules that the rules themselves would not apply.

What the service does is as it was decided: it applies nothing of a prompt that is not plain. The test that holds that of the service stands. What no longer stands is that a person stood between an offer and the search.

**The line that said what one press did is given up with the press.** It said how many things were added, and how many areas a firm budget among them left out, from the ranking that followed: the founder had found on 2026-09-25 that a budget which leaves areas out must not be taken in silence. A firm budget that is taken of a sentence that is no plain list is now said as one that is taken of a plain list is: its chip says "firm limit", the line that says what happened says how many areas were ranked, and the map and the table of all areas say which were left out. No line counts them.

### What it risks

Each of these was known when this record was written, and was the reason it asked. None was mended by the amendment. Each now reaches the ranking where it reached an offer.

| What | How often, where it was measured | What a person now sees |
|---|---|---|
| A reading that is backwards, with Burro's guess on it | 1 of the 113 sentences a model read, on the second measurement, which is 0.9 in 100: the floor allows 1 in 100, "with nothing to spare" | The search is moved the wrong way, and its chip says "assumed" |
| A wish that the words turn round, in words core does not list | The sentences this record was written for: "Pubs are so noisy", "Some want pubs", "I want pubs. Actually I do not want pubs." The rules offer each with more and fewer, and guess at neither | **Areas with more pubs come first**, under a chip that says more pubs were assumed. It is the misreading that costs trust, and asking was what kept it from the ranking |
| Somebody else's wish | "My mum is after a park" is offered as a wish for a park, in every look | It is applied as the person's own |
| A model that is careless, or means harm | A stand-in that raises whatever a sentence names was marked as the guess, backwards, on 73 of the 820 cases of the evaluation set | Whatever it raises and the guard lets through is applied |
| A number that is no budget | "I have a 50k deposit" was a budget of £50,000, with the guess, in one look of four | A budget of £50,000 is set, as a guide |
| What a model reads differs from one asking to the next | Of ten sentences asked four to six times, five came back one way and five did not | The same sentence may rank areas otherwise the next time it is typed |
| The rules alone, where every guess is taken | Of the 901 sentences that are held as cases, 42 hold a guess of the rules. To take every one leaves 2 right and 39 in part, and one where nothing that was asked for was guessed. None is backwards | Most such searches hold part of what was asked, and say what was not read |
| An offer with two ways and no guess, taken as the gentler | Not measured. The scorer takes what carries a guess, and nothing else | Not known |

### What holds it

| What | Where it is held |
|---|---|
| What a model may read, which way, how much and how firm are code's to say, and some things are never offered from a model | The guard, in the service, with the thirteen checks of the contract, section 8.2. Nothing of it was changed |
| No area is left out on a guess | A limit is firm only where the person's own words make it one, by core's two lists. A journey is never taken as a firm limit, since it is estimated from distance ([0027](0027-a-journey-is-estimated-from-distance-until-a-timetable-is-held.md)). `test_no_limit_leaves_an_area_out_unless_the_service_says_one_press_may_set_it`, and `test_a_journey_is_taken_as_a_guide_though_the_words_give_a_firm_limit_and_the_guide_is_said_to_be_assumed` |
| The website builds no edit of its own | `test_whatever_is_taken_is_a_way_the_service_gave_with_the_edits_it_gave` |
| What was applied is in sight, where a person looks when they press Search | Directly under the box: what Burro understood, as chips. Nothing stands between the box and it |
| What nobody said is said to be assumed | The word on the chip, as it was. It is never told by colour alone |
| One press takes a thing off | The cross of its chip. "Refine search" holds every setting with its value, and a chip opens the control of its thing in place |
| A wish counts as a mention counts | The edits are the service's own, and a wish that one press took was taken at a mention or a small step. Nothing is taken at the most a thing can count |
| Recorded crime, and what counts who lives somewhere, wait for a person | The website takes neither, and says what it left: `test_what_counts_who_lived_somewhere_is_never_taken_and_is_said_to_be_left`, in `apps/web/src/lib/search/takes.test.ts`, and beside it, until 2026-09-27, a test that held the same of recorded crime. *Since then recorded crime is taken where the service says the person's own words name it, and the tests that hold it are `test_what_counts_recorded_crime_is_left_unless_the_service_says_the_persons_own_words_name_it` and `test_what_counts_recorded_crime_is_taken_where_the_service_says_the_persons_own_words_name_it`: "The amendment of 27 September 2026", below.* Which thing is of which kind is read from what the service says of every measure and of the recipe of every vibe, and is written nowhere in the website. The reducer still turns away an edit of recorded crime that is only inferred |
| What was not read is said | The line under the box, and the words in the box that it points at |
| Nothing a person typed is kept, and what was applied is kept no longer than the search | [0005](0005-raw-prompts-are-never-stored.md), [0011](0011-nothing-is-kept-for-a-search.md) |

**What does not hold it.** No test holds that a wish which was turned round is not applied: the tests that held that nothing was ranked from what was noticed until the person chose were of the rule that went. The words that turn a wish are core's lists, and English has more of them than any list: that is how this record began.

### What follows

- **The floor cannot be met as it is written.** Its first row was that no reading of a model's is applied without a press, and it was a test and not a rate. A model was turned on where Burro is hosted on 2026-09-26, under the floor as it then stood. Whether a model stays on while what it reads is applied unasked is the founder's to say, and the first thing to confirm below.
- **What the floor counted as offered with a guess, it now counts as applied.** "A backwards reading offered with a guess marked: 1 in 100 sentences" is a backwards search in a hundred. The measurement that holds it is of one model, on 113 made-up sentences, and the record says of it that it is a fit and not a measurement.
- **The legal drafts said that a person chooses.** [The terms](../legal/terms-of-use.md), section 5, and [the privacy notice](../legal/privacy-notice.md), sections 3 and 4, were brought to the change. Each marked as not yet built that nothing a model reads is applied until a person chooses it. It is now decided the other way.
- **The iPhone app still asks.** It draws an offer in its four parts and takes a choice by its id, as the website did, and was not changed.
- **The drawings of a question are met nowhere.** The rabbit on his hind legs, the dialogue box and the carrot were drawn where Burro asked ([0033](0033-the-website-looks-like-the-map-of-a-gentle-game.md), as amended). *The carrot is met still, where it lay besides: beside the choice in hand in the list of examples and in the list of places that match a name.*
- **The box still sends what was added, and no word twice** ([0036](0036-the-box-sends-what-was-added-and-keeps-counts.md)). Words are read once something came of them, and what comes of them is now applied.

### To confirm

Each was decided for the founder, from what they asked, and is theirs to overturn.

1. **A model may stay on while what it reads is applied unasked.** The floor's first row is given up. The other rows stand, and are of what is now applied.
2. **Where Burro cannot tell which of two things was meant, it takes the gentler.** A limit is a guide, a thing counts for more of what its name says, and a name that several places bear is the first the service gives. The second of these applies the sentences this record was written against. To take nothing of a thing that runs two ways with no guess would lose the wish and keep the trust: it is built, and is the one line `WHERE_BURRO_CANNOT_TELL`. *That line was turned that night, and the second of these stands of a thing that runs one way alone: "Amended that night", below.*
3. **Recorded crime, and what counts who lives somewhere, are not taken.** They wait for a person, in the settings, and one line says that they were left out. It is the one exception to what the founder asked, and keeps two promises of the product. It means that a person who typed "gritty" in a sentence that is not plain is not given Gritty until they choose it. To overturn it is to change the rule on recorded crime and rule 8.
4. **What was left out is said in a line, and nothing is asked.** A person who reads the line finds the thing under "Refine search". One who does not read it has a search that holds less than they typed.

### Amended that night: where the words give no way, neither is taken

The website was driven against the service that night, sentence by sentence. Two things were found of the fourth row of the table of ways, which took more of a thing where the service named no way and marked none as its guess.

| What was typed | What the service offered | What the website made of it |
|---|---|---|
| "Leafy and quiet, near Gorsebeck", and "visiting my mother in Pellam Cross": each names a place that is an area as well | A rule for the area, two ways and no guess: to look only there, or to leave it out | It took the first. Seen in a browser after the first sentence: one area was ranked and 21 were left out, on a guess, under a chip that said "Gorsebeck, only" and not that it was assumed |
| "Pubs are so noisy", and a wish for fewer of a thing in a sentence that is no plain list | The thing, more or fewer, with no guess | More of it was counted, under a chip that said "assumed". It is the first thing this record risked, and it was seen to happen |

**Decision.** Where the words give no way of a thing, which is where the service names no way that one press may take and marks none as its guess, the website takes neither way of two kinds of thing. Each is named in the line of what was left out, which says why when it is opened.

| Left, where the words give no way | Why | What the line says of it |
|---|---|---|
| A rule for an area: to look only there, or to leave it out | Whichever is taken, areas are left out, so neither is the gentler. That no area is left out on a guess was decided that evening, and this was a way round it | That Burro noticed the name of the area and could not be sure what was wanted of it, so it left every area in. And how to say either: the word "only" before the name, or the button that hides an area, on its result |
| A thing that runs two ways: more or fewer, or towards either end of a scale | More of it may be the wrong way round, and a ranking that is turned round costs more trust than a wish that waits | That Burro could not tell which way it was meant to count, and that it can be added under "Refine search" |

**So four kinds of thing are never taken without being asked**: what counts recorded crime, what counts who lived somewhere, a rule that leaves areas out, and a thing whose words give neither way. The first two wait for a person whatever the words say, because a promise of the product keeps them. The other two are taken wherever the words give the way: "only in Foxholt" looks only there, and "fewer pubs" in a plain list counts fewer.

| Matter | What stood that evening | What stands now |
|---|---|---|
| A thing that runs one way, with no guess | More of what its name says | The same |
| A thing that runs two ways, with no guess | More of what its name says, under a chip that said "assumed" | Neither. It is named among what was left out. One line has more of it taken: `WHERE_BURRO_CANNOT_TELL` in `apps/web/src/lib/search/takes.ts`, which is on `left` where it was on `more` |
| A rule for an area, with no guess | The first way the service gave, which looks only there | Neither, and every area stays in. No line chooses otherwise. Such an offer is told by the edits the service gives with its ways, and by no name |
| A rule for an area that the service names or guesses | Taken | The same |
| A limit, a place that several places bear the name of, and what is never taken | Rows 1, 2, 3 and 5 of the table of ways, and the table of what is never taken | The same |
| The service | Applies a plain prompt, and offers what it noticed of any other | The same. Nothing of it was changed for this |

**What it gives up.** More of what the founder asked for on their second walk. A thing that was noticed and left is in the search only once a person adds it, and a person who does not read the line has a search that holds less than they typed.

**What it mends of what this record risks.** The second row of "What it risks": a wish that the words turn round, in words core does not list, no longer reaches the ranking where the service marks no guess. It reaches it still where the service guesses, or a model does, and the guess is wrong. The last row, which was not measured, is of a state that is no longer met.

**What holds it.** `apps/web/src/lib/search/takes.test.ts` holds each row of the table above, and that a rule for an area is taken where the service says the words give it. `said.ts` beside it holds what the line says of each.

**To confirm, of that night.** Each was decided for the founder, and is theirs to overturn. They are the fifth and the sixth of what the amendments of 26 September leave to confirm.

5. **Where the words give no way of it, a rule that leaves areas out and a thing that runs two ways are left, and said to be.** Decided that night, from what driving the website found. It gives up more of "assume they want it to be added" than the evening did: a person who wrote that pubs are noisy has nothing of pubs in their search until they add it. One line has more of such a thing taken, as it was for an evening.
6. **A word that the rules read more ways than one is taken every way.** "Affluent" and "posh" are read as the mix of brands, as what homes sell for and as the share of homes in the higher council tax bands, and each is taken and marked "assumed". The amendment of 25 September kept such readings from one press, and the record of household income has the last of them offered and never applied, because it follows household income at 0.71 ([0028](0028-household-income-is-shown-and-never-ranked-on.md)). It was left as the evening built it, and is the founder's to decide knowingly: `OF_A_WORD_READ_SEVERAL_WAYS` in `apps/web/src/lib/search/takes.ts` has none of them taken.

## The amendment of 27 September 2026

**What was found.** Since the evening of 26 September the website takes what is offered and asks nothing. The service had been built for a person who chooses. Of a thing that runs two ways it offered both, though the words plainly named one, and it said of no offer whether the words named the thing. So a client that asks nothing could not keep two promises of the product but by the name of a measure: that recorded crime counts only when a person asks for it by name, and that some things are offered and never applied. Driven in a browser on 2026-09-27: "Honestly, somewhere calm" was answered "Burro has not ranked any areas yet. Left out of your search: Going out". "I never use the station" ranked 22 areas under a chip that said "Nearer a station assumed", and the first reason of the first result was how close its station is.

### Decision

**The service says more of each offer, and the website reads what it says. The service still applies nothing but a plain prompt, and a model still never ranks, scores or describes a place.**

| Matter | What stood | What stands now |
|---|---|---|
| The way the words give of a wish | The rules offered a measure or a vibe wherever it was named, and chose no way of it | Where the rules would apply the sentence a thing stands in, were it all that was typed, the way they give is Burro's guess, and the way one press may take. What is said of the words alone is left out of the sentence first, as "honestly" and "I think" are: a closed list of 16, in core |
| A thing the words turn round | Offered every way | Where the rules read the turn, their way is the guess: "honestly, no station" is to stop counting it. Where they cannot, no way that counts the thing for more is offered, and nothing is the guess: what is left is to stop counting it, or nothing, with a sentence that says why |
| A thing that runs two ways, which the words turn round where the rules cannot read the turn, as "I hate pubs" | Both ways | Both ways, and no guess, so the website takes neither. It was built a second way, which offers only the way against the thing: one line chooses, `WHERE_A_TURN_IS_NOT_READ` in `services/api/src/burro_api/guard.py` |
| What the words do not say is the person's own | Offered every way | Offered every way, and it waits for the person: a wish that may be somebody else's, a nuisance that is only named, a thing in a list after one that is turned away, and a thing under a heading that core does not list as heading what is wanted |
| What an offer says of itself | Its ways, its guess and what one press may take | Those, and two things more. `by_name`: the person's own words name what the offer counts. `only_by_choice`: it waits for a person, and a client that asks nothing takes no way of it. What counts who lived somewhere waits whatever the words are. What counts recorded crime waits wherever the words do not name it. So does a measure that a decision holds to be offered and never applied, which is the share of homes in the higher council tax bands ([0028](0028-household-income-is-shown-and-never-ranked-on.md)) |
| What the website never takes | What counts recorded crime, and what counts who lived somewhere, which it told by what the service says each measure is of | Whatever the service says waits for a person. It takes what counts recorded crime where the service says the person named it: to type "gritty" is to ask, and to type "posh" is not, though the same vibe is offered for both. What counts who lived somewhere is never taken, whatever is said of it. The website reads no word, and names no measure |
| A rule for an area | Taken where the service named a way of it or marked one | Taken by the way the service marks as its guess, and by no other. Its chip says that it was assumed |
| A thing the words turn away, where all that is offered is to stop counting it and the service marks that as its guess: "honestly, no station" | To stop counting a thing was no way of taking it, so nothing was taken | The thing is counted no longer, and its chip says that it is off. Such a thing counts a little in every search until a person says otherwise. One line leaves it counting, as it was: `WHAT_THE_WORDS_TURN_AWAY` in `apps/web/src/lib/search/takes.ts` |
| A word that is read more ways than one, as "affluent" is | Every reading was taken | One reading is taken: the one the service marks as its guess, or else the first it gives of those that may be taken. The others are named in the line of what was left out. One line has every reading taken, or none: `OF_A_WORD_READ_SEVERAL_WAYS` in `apps/web/src/lib/search/takes.ts` |
| A plain sentence that leaves one word unread, behind a model | Applied by nobody | Applied by the rules, and handed to no model |
| "At the very most" | No firm limit | A firm limit, as "at most" is, of money and of minutes |
| "Somewhere cheaper", typed into a visit | Turned away | Answered with a sentence that says a visit has no budget |

[The contract](../design/contract.md), section 8.2, has every rule and how each is worked out. The contract stays at version 3: each of the two fields has a default and is not required.

### What it did

Held to the evaluation set, which was 1,026 sentences on 2026-09-27, by the scorer's own judgement of the search that follows: a client that takes what is offered and asks nothing read 87 sentences backwards, made an edit nobody asked for in 39, and was right in 674. It reads 31 backwards and 33 unasked, and is right in 704. All 132 plain cases are applied, as they were. `services/api/tests/test_what_a_client_that_asks_nothing_takes.py` holds the three counts as a ceiling and a floor.

### What it still gets wrong

- **A client that asks nothing still reads 31 sentences of 1,026 backwards.** They are in words core does not list: "a station would drive me up the wall", "parks aren't important to me", "I'm done renting", "I earn 60k".
- **What is said of a home or of a journey with no guess is still taken.** "I earn 60k" is taken as a budget. To hold them to the guess mends 9 sentences and loses 35 that are right, so it was left.
- **Where the service could not read a turn, the thing still counts as it did.** Of "I never use the station" nothing is taken, and the station counts a little, as it does in every search until a person says otherwise.

### To confirm

Each was decided for the founder, and is theirs to overturn.

1. **Where a turn is not read, both ways of a thing that runs two ways are offered, and neither is taken.** To offer only the way against the thing reads "I hate pubs" rightly, and reads "you can't beat a good pub" backwards: on the 1,026 sentences it is right in 724 and backwards in 41, where this is right in 704 and backwards in 31. The way that shows less was chosen.
2. **What homes sell for does not wait.** The record of household income has the higher council tax bands offered and never applied, and says that what homes sell for stays as it is served, though it follows household income at 0.58. So of "slightly affluent" the website takes one of the mix of brands and what homes sell for, and never the bands. To have it wait too is one name added to `OFFERED_AND_NEVER_APPLIED` in `packages/core/src/burro_core/catalogue.py`.
3. **One reading of a word that is read several ways is taken.** It overturns the sixth of what the amendments of 26 September left to confirm, which had every reading taken. None is one line.
4. **A thing the words turn away is counted no longer, where the service reads the turn.** It is the one case in which the website takes a thing off that a person did not take off themselves. One line leaves it counting.

