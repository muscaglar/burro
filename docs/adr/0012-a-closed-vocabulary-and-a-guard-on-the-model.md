# 0012. The reader reads by what it knows, and a model is held to the reader

Status: accepted, 2026-09-23. Builds on [0002](0002-deterministic-core.md) and [0005](0005-raw-prompts-are-never-stored.md). Three points go further than what was decided and are for the founder to confirm.

## Context

Burro turns a sentence into typed edits in two ways: by rules, which need no model, and by a model, whose answer is checked by code. A wish that is not read costs little, because the controls are on the screen. A wish that is read backwards costs trust: "no pubs" that puts the area with the most pubs first.

The rule-based reader was put right twice by listing the words that turn a wish round. Each time an adversary wrote a few hundred sentences and a hundred of them still came out as the opposite of what was asked. English has too many such words, and people mistype them.

The guard on the model had the same fault one step removed. It kept what a model raised unless the request held a listed sign of doubt, and it let a doubt anywhere silence the model everywhere. Thirty ways were found through it: a name put together across a bracket, "only" answered as "exclude", a hard budget nobody gave, and every sentence the list of doubt did not cover.

## Decision

**The reader.** It reads a sentence only when it knows every token in it: a phrase of the lexicon, a name of the release, a number, a plain word from a short list that is written down in one place, or a word it has an explicit rule for. Anything else leaves the sentence unread, with no edit and `other` in `unmet`. A sentence ends only at a full stop, a question mark, an exclamation mark or a line break. A question makes no edit. Every edit says which words of the text it rests on, as offsets.

**The model.** It must copy, for each edit, the words of the person's that the edit rests on. The code finds those words in the text as typed, in one sentence, and asks the reader what it made of that sentence:

- In a sentence the reader knows, the reader's reading is the whole of it. A model's edit is kept only if the reader made one of the same kind there, and what is applied is the reader's.
- In a sentence the reader does not know, a model may read a wish for a thing the reader has no phrase for, and no more. It is raised only where the sentence holds no word that turns and no word of the written list of doubt, and it is marked as inferred.
- A journey, a budget and a rule about an area are the reader's alone.
- A name is the whole of a name, as typed, side by side.
- On a request about who lives somewhere, only the reader's edits are kept. A model that answers off topic does not overrule the reader.

**Where the words stand** is returned to the caller by route 1, and never logged or stored.

The contract, sections 8.2, 9.2 and 13, holds the rules in full and what each was measured to cost.

## Consequences

- The reader declines more plain sentences: of 60 held out, 46 are read where 55 were. It says what it could not read.
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

The next step is decided and not yet built: the reader applies a prompt only when the whole of it is a plain list of things wanted or not wanted. For any other prompt it applies nothing, and offers what it noticed for the person to confirm, with the direction theirs to choose. Until that is built, the rule-based reader is a fallback to be used with care, and the sentences above are kept as cases in `evals/`.

## To confirm

1. **In a known sentence the model adds nothing.** The decision kept a model's edit wherever the sentence held no doubt. It costs "somewhere for the kids", which a model reads as a wish for playgrounds and the reader reads as nothing.
2. **In an unknown sentence a model may not touch a thing the sentence names in the reader's own words, nor add a journey or set a budget.** The decision let it, where no doubt was listed. This is what took the stand-in from 52 to one. It costs 11 of the 230 plain sentences.
3. **An area rule is never the model's.** The decision kept one where the reader read none and no doubt was listed. It costs "cross Cindermoor off my list".

To go back to the letter on any of the three is a small change in `services/api/src/burro_api/claude.py`, and the floor and the ceiling in its tests say what it would cost.
