# 0012. The reader applies a plain prompt and asks about any other, and a model proposes

Status: accepted, 2026-09-23. Amended the same day: the reader now applies a prompt only when the whole of it is plain, which was the next step this record named. Amended 2026-09-24: the guard on the model went, and nothing a model reads is applied. The model proposes, the person confirms, code checks. Amended again that day: what makes a limit firm, and then what is said about a thing, which the foot of this record says. Builds on [0002](0002-deterministic-core.md) and [0005](0005-raw-prompts-are-never-stored.md). Three calls of the amendment are for the founder to confirm.

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
8. **"Add all" adds less than a person may**: a wish or a vibe at a mention or a small step, the tenure, a budget as a guide, a journey as a guide to a place named in full. Never what leaves areas out, what runs two ways with no guess, a journey to a place that is yet to be chosen, or recorded crime.
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
2. **"Add all" never adds anything that leaves areas out.** Where the guess is a firm limit, it adds the guide, and says that the limit can be made firm.
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

The lists are core's, `FIRM_OF_MONEY` and `FIRM_OF_MINUTES`. The rules read them in a plain prompt and in an offer. The guard on a model reads them where a model called a limit firm, and the scorer of the evaluation reads them too, so the three cannot disagree. A budget or a journey that is only noticed is offered as a firm limit where the words say so, and "add all" still adds nothing that leaves areas out.

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
- **A turn in another sentence, in the heading of a list, or in words core does not list.** "A park? No thanks.", "Dealbreakers: pubs", "a station would drive me up the wall". They are most of the 73.
- **A way a model adds to a question.** "Everyone tells me to live near the station but the trains would drive me mad": in one look of four the model added more lines nearby, and it stands as a third way of the rules' question, with no guess.
- **What a model reads differs from one asking to the next.** Of ten sentences asked four to six times, five came back one way and five did not, before and after. The founder's sentence came back three ways in six looks: with a guess at culture, without one, and once with the notice about who lives somewhere and no journey. The order of a model's edits no longer changes what is offered. What it reads, which words it quotes and whether it flags a sentence still do, and code cannot make those the same.
- **The rules' question about a place is dropped where a model reads.** The rules alone ask which place "Chancery lane" is. With a model on, the question is asked only where the model reads the journey too. The scorer counts it as a reading of the rules lost, on the founder's sentence and on two cases like it. It was so before this amendment, and is not mended by it.

### To confirm, of what is said about a thing

1. **A wish of a partner's is asked, and not guessed.** The evaluation set says two people make one search. Either the cases change or the guard does.
2. **A word for a home alone names no end.** "A flat" stays a question, and "houses not flats" is Houses.
3. **Where a model names no end of a scale, the guess takes the end the words name only where they turned one away.** Let through for every end that is only named, a stand-in that raises whatever is named was marked backwards on eleven cases more.
