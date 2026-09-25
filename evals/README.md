# evals

How well does Burro read what a person types? This folder answers that, for any reader, in under a second, with no model and no network.

Burro turns a sentence into typed edits to a search. Two readers sit behind one interface: the rules in `packages/core`, and a model in `services/api`, which one of four providers runs. `evals/reader` holds made-up sentences, what a correct reading of each one is, and a scorer that runs a reader over all of them.

| Path | What it is |
|---|---|
| `reader/cases/*.jsonl` | The cases, one file for each kind of sentence. Written by hand |
| `reader/score.py` | The scorer. Standard library and `burro_core` only |
| `reader/floor.json` | The least a reader may score before a run fails |
| `reader/controls.py` | Two readers whose faults are known, to measure a real one against |
| `reader/stand_in.py` | Measures the guard on a model with two stand-ins, and no provider. It imports the API |
| `reader/answers/` | What one model answered to 112 made-up sentences, word for word, and the 30 cases written for that measurement |
| `reader/replay.py` | Reads those answers again through the reader the service uses, with a stand-in that hands each one back. It calls no provider, and imports the API |
| `reader/test_score.py`, `test_stand_in.py`, `test_replay.py` | Tests of the scorer itself, of the stand-ins, and of the answers on disk against the floor |
| `reader/baseline/` | The outcome of every case at the last measurement, one file for each reader |
| `reader/BASELINE.md` | The last measurement, in words, with its date |

## Run it

```
uv run python evals/reader/score.py            # the rule-based reader, every case
uv run python evals/reader/score.py --check    # check the cases and run no reader
uv run python evals/reader/score.py --group negatives --show all
uv run python evals/reader/score.py --case neg-012
uv run python evals/reader/score.py --against evals/reader/baseline/rule.json
uv run pytest evals/reader                     # the scorer's own tests
```

It exits 0 when the run passes, 1 when it fails, and 2 when a case cannot be scored as it is written.

A run fails if:

1. **any case is reversed**, whatever the rest looks like, or
2. the share read correctly is below `correct_share` in `floor.json`, or
3. more cases than `unasked_ceiling` hold an edit nobody asked for, or
4. the share of the cases marked `plain` that are read correctly is below `plain_correct_share`, which is 1: a plain prompt must be applied.

A run of part of the set, with `--group` or `--case`, is held to the first rule only.

## What the report says

Every case ends as one of these. The worst thing found decides.

| Outcome | What happened |
|---|---|
| **REVERSED** | The reader did the opposite of what was said. It raised what was turned down, added a journey to a place the person wants distance from, or made the other rule for an area. The sentences are always listed |
| unasked | The reader made an edit nobody asked for: a wish of someone else's, a number the words do not give, a workplace that is over. The sentences are always listed |
| declined | The reader read nothing of what was asked, and did not offer all of it. The form is still on the screen, so this costs little |
| in part | The reader read some of what was asked, or gave a notice or asked a question that was not called for |
| suggested | The reader moved nothing, and offered every thing that was asked for, with the direction asked for among the choices. It is neither correct nor reversed. A suggestion that offers only the other direction is declined |
| correct | Everything asked for happened, and nothing else did |
| failed | The reader raised an error. Only a model-backed reader can |

A suggestion cannot be reversed or unasked, because nothing moved. It is judged by what a person could choose: the scorer tries each way of choosing among what was offered, one choice of each suggestion or none, and the case is `suggested` if one of them leaves the search as the case says it should be.

Under the table are more lines. Some cases ask for something, and some are right to leave alone: a question, a wish of someone else's, a sentence about the weather. A reader that does nothing is right about every case of the second kind, so one share for the whole set flatters it. The lines give each kind its own share, and for the first kind how many were read or offered. A case that is right to leave alone stays correct when nothing moved, and the suggestions made there are counted on a line of their own: "offered where nothing was asked". The last line says how many prompts were applied, how many became suggestions and how many were declined.

The scorer prints counts, case ids and sentences from the cases. It never prints what a reader answered, and of an error it keeps only the name of its class.

### What was offered

Nothing a model reads is applied: it is offered, and the way Burro reads a thing is marked as its guess (contract, section 8.2). So a reader that marks a guess is judged a second time, by what a person would get who pressed every guess. The rules mark none, and their score is as it was.

| Outcome | What happened |
|---|---|
| **APPLIED WITH NO PRESS** | The reader applied an edit the rules did not make. No path may |
| **NEVER TO BE OFFERED** | An offer holds what is never offered from a model: a vibe that counts recorded crime, recorded crime the words do not name, a firm limit that the words against its own number do not give, a number for a weight, a rule for an area as the guess, a journey to a place the person did not type, a number of minutes or an amount they did not type, a way of travelling no word names, and an offer of a model's that rests on a wish about who lives somewhere. It is judged from the offer and the sentence, and asks nothing of the reader. It does not know a word about wealth: core lists none yet |
| **BACKWARDS GUESS** | To press every guess does the opposite of what was said |
| backwards, unmarked | A way a model added, which is no guess, would do the opposite if it were pressed. The rules' own ways are not counted: they are there whoever reads |
| unasked guess | To press every guess makes an edit nobody asked for |
| not read, in part, right | As above, of the search a person would have who pressed every guess |

A run of such a reader fails if anything is applied with no press, if anything is offered that is never to be offered, if a right reading of the rules is lost, if more than 1 case in 100 is a backwards guess, or if more than 1 in 25 of the cases that are right to leave alone holds a backwards way that a model added.

### The two controls

```
uv run python evals/reader/score.py --reader nothing
uv run python evals/reader/score.py --reader keywords
```

`nothing` reads nothing. It never reverses and never invents, and it is the score to beat. `keywords` raises whatever the words name, whatever is said of it. It reverses more than a hundred cases. If it ever passes, the cases have lost their teeth, and a test says so.

## How a case is judged

The scorer hands the reader the sentence and the search as it stands, puts the edits through the reducer as the service does, and compares the search before and after. It judges what happened and never how the reader got there. So an edit the reducer turns away, such as crime read into the word "safe", has moved nothing.

Weights are compared after the defaults have given way (contract, section 5.3), so a default that shrinks because something else was said has not moved.

A thing has **risen** if it counts for more in the direction it is wanted. For pubs that is more pubs. For noise, air and crime, which have one direction, a higher weight is a wish for less of them: "less noise" raises `feature:noise_exposure`. A thing has **fallen** if it was taken off, turned down, or turned to `less`: "fewer pubs" is pubs with a weight and the direction `less`, and that is a fall.

## The cases

One case is one line of JSON.

```json
{"id": "neg-003", "text": "not near a station", "tenure": "rent", "expect": {"fall": ["feature:station_walk"], "not_rise": ["feature:station_lines"]}, "why": "not near, of a thing with a default weight"}
```

| Key | What it holds |
|---|---|
| `id` | A name that never changes, so that two runs can be compared |
| `text` | What the person typed, 1 to 600 characters |
| `tenure` | `rent` or `buy`: where the toggle stands when they type |
| `expect` | What a correct reading is. Every key below is optional |
| `why` | One line on what the case is for |
| `held` | Optional. What the search already holds, for a follow-up: `journeys`, `areas`, `weights`, `tags`, `budget`. A vibe that is held towards the low end of a scale is given a weight below nothing |
| `plain` | Optional, `true` or `false`. `true` says the prompt is plain by the grammar of the contract's section 8.2, and must be applied. `false` says it is not, and that any edit that is applied is unasked |

Anything `expect` does not name must stay as it was. A reader that moves it has made an edit nobody asked for.

**Features and vibes.** Each is written `feature:<id>` or `tag:<id>`, with the ids of the contract's section 3. A scale rises towards its high end and falls towards its low end: "calm" is a fall of `tag:pace`, and "a house with a garden" a fall of `tag:homes`.

| Key | Meaning | If the reader does otherwise |
|---|---|---|
| `rise` | Each must rise | Unmoved is missed. Lowered is reversed |
| `fall` | Each must fall | Unmoved is missed. Raised is reversed |
| `rise_any`, `fall_any` | A list of lists. One of each list must move, and none may go the other way. For a wish that more than one id can hold: "quiet" is the tag or the noise feature | None moved is missed. One the other way is reversed |
| `not_rise` | The person is against it. To lower it and to leave it are both right | Raised is reversed |
| `not_fall` | The person is for it, or may be. To raise it and to leave it are both right | Lowered is reversed |
| `still` | It is named in the words and nothing is asked of it. The same as not naming it, written down to show the trap | Moved is unasked |
| `free` | It may go either way, because the words can fairly be read both ways | Nothing |

**Journeys**, under `journeys`. A place is written by its name or an alias in the release.

| Key | Meaning |
|---|---|
| `add` | The search must hold a journey to each. One is a name, or `{"to": ..., "mode": ..., "max_minutes": ..., "strictness": ...}`. A field that is left out must be what nobody chose: public transport, 45 minutes, soft. `"any"` accepts whatever the reader chose |
| `not_add` | The person wants distance from the place, or the workplace is not theirs. A journey to it is reversed |
| `may_add` | A journey to it is accepted and not required |
| `remove` | A journey the search holds must go |

**Areas**, under `areas`: `exclude`, `only`, `clear`, and `not_exclude`, `not_only`, `may_exclude`, `may_only`, which work as the keys for journeys do. The other rule for an area that was to be excluded is reversed.

**Budget**, under `budget`: `amount` (a number, or a least and a most), `not_amount` (numbers the words turn down, or that are no budget at all, such as a salary), `segment`, `strictness`, `clear` (the amount must be taken off) and `may_set`. `"any"` works as it does for a journey.

**The rest.**

| Key | Meaning |
|---|---|
| `tenure`, `not_tenure` | The tenure the search must end in, or must not be moved to |
| `notice` | `none` by default, so a notice that is given without cause is a fault. `neutral_places` and `off_topic` must be given. `any` accepts either |
| `unmet` | Categories the reader must report as unmet, such as `driving` |
| `ask` | `no` by default: a question where none was open is a fault. `ok`: to ask is as good as to act. `must`: the reader must ask and must not guess |

### The groups

| File | What is in it |
|---|---|
| `plain_wishes` | Things wanted, in everyday words. Rules for `only`. What Burro cannot answer |
| `budgets` | Amounts, sizes and tenure. Ranges, slang, salaries and deposits |
| `journeys` | Workplaces and caps. Former workplaces, and a minimum distance written like a cap |
| `negatives` | Things not wanted, said plainly and said by idiom. Areas to avoid. A tenure that is left |
| `double_negatives` | Two negatives that make a wish, and mild ones that make half of one |
| `typos` | Broken contractions, misspelt things, names with a letter lost |
| `lists` | Bare lists, headings, lists that a doubt follows |
| `questions` | Questions that ask nothing of the search, questions that mean no, and polite requests |
| `other_peoples_wishes` | A partner's workplace, a child's need, advice that is set aside |
| `who_lives_there` | Requests about residents, a community's amenities, and innocent words that look like either |
| `crime` | Crime asked for outright, implied by "safe", and named as a subject |
| `off_topic` | Sentences about anything else, some holding words of the catalogue |
| `other_languages` | Twelve languages, and sentences that mix two |
| `very_long` | 300 characters and more, as a person writes when they tell the whole story |
| `very_short` | One to three words |
| `plain_prompts` | Prompts that are plain by the grammar, and must be applied whole: a list of things, a budget, a journey. Each is marked `plain` |
| `suggestions` | Prompts that are not plain, of which nothing may be applied. What they ask for must be offered |
| `vibes` | Three sentences for each vibe of the committed release. The words of the way gritty is not built in it are held by core's own tests |
| `whole_searches` | The whole of a search as a newcomer types it, and each part of one alone: hedged wishes, a word for a smart area or for character, a journey given as a range or to a place the release does not hold, and a home to rent or to buy. `whole-035` is the founder's own test sentence, word for word and by their consent. It is the one sentence of the set that is not made up, and it names a place the release does not hold |

## Add a case

1. Write the sentence the way a person would type it. Do not start from the lexicon.
2. Decide what a careful human would do with it. Where two readings are fair, use `rise_any`, `not_rise`, `not_fall`, `free` or `"any"`, and do not pick one.
3. Add one line to the file for its kind. Give it the next id of that file. Never reuse or renumber an id.
4. Use the names of the synthetic release for places and areas. `--check` refuses a name the release does not hold.
5. Run `uv run python evals/reader/score.py --check`, then the scorer.
6. If the rule-based reader reverses it, you have found a fault in the reader. Leave the case in, and let the run fail until the reader is put right. Do not weaken the case.

When the reader improves, raise the floor. When a case turns out to be wrong, change the case and say why in the commit. Do not lower the floor to make a change pass.

## Whose words these are

**Every sentence here is made up.** ADR 0005 says that what a person types is never stored, and that an evaluation set of real prompts is a separate table, filled only with explicit consent. That table does not exist. So:

- A real user's words never enter this folder. Not copied, not reworded, not with the name taken out.
- Not from a log, because nothing typed is logged. Not from a bug report or a support email, unless the person who wrote it has said in writing that this sentence may be published in a public repository.
- A case written after a bug report is written new, from the kind of fault it showed, in your own words.
- Every place and area is a name of the synthetic release. No case holds a real address, workplace or name of a person.

This repository is public. Anything added here is published.

## Measure the guard with a stand-in

```
uv run python evals/reader/stand_in.py            # about a minute
uv run python evals/reader/stand_in.py --show     # and list each case the settings move
```

Nothing a model reads is applied: it is offered, under the checks of the contract, section 8.2. This measures those checks with no model and no provider. Two stand-ins answer in a model's place, through the reader the service uses.

| Stand-in | What it answers | What it shows |
|---|---|---|
| `right` | What the case says a careful person would do | The most a model could add that reads every sentence well |
| `backwards` | Every thing the sentence names, raised, whatever is said of it | What the checks let a careless model do |

Each is run twice: sent the words alone, and sent the search settings with them, as `BURRO_MODEL_SENDS_SETTINGS` decides in the service. A stand-in uses only what it is sent. Each case is scored with the words a model could best rest its edits on: the whole text, or one sentence of it. It exits 1 if any case ends otherwise when the settings are sent.

Measured on 2026-09-24, on the 781 cases the set then held. 39 cases were added after it, 35 of `whole_searches` and 4 of `who_lives_there`. By what became of the search, which is what the rules made of it:

| Reader | Correct | Suggested | In part | Declined | Unasked | REVERSED |
|---|---:|---:|---:|---:|---:|---:|
| The rules alone | 408 | 232 | 5 | 136 | 0 | 0 |
| `right`, sent the words alone or the settings as well | 431 | 279 | 5 | 66 | 0 | 0 |
| `backwards`, sent the words alone or the settings as well | 408 | 233 | 5 | 135 | 0 | 0 |

By what a person would get who pressed every guess:

| Reader | Right | In part | Not read | Unasked guess | BACKWARDS GUESS | Never to be offered | Applied with no press | Readings of the rules lost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `right` | 398 | 44 | 114 | 1 | 0 | 0 | 0 | 0 |
| `backwards` | 218 | 40 | 172 | 45 | 88 | 0 | 0 | 0 |

What it says:

- **Nothing is applied, whatever a model answers.** No case is reversed and none holds an edit nobody asked for, for either stand-in. The two cases that came through the guard that went, `crime-040` and `sugg-004`, no longer do.
- **No reading of the rules is lost.** The stand-in that quotes the name of a place alone once lost the minutes the rules had read, on `list-034` and `ask-015`. A test holds both.
- **The checks do not hold the floor against a model that raises whatever is named.** 88 of 781 cases are a backwards guess for the careless stand-in: a turn that stands in a heading, "Dealbreakers: pubs", after the list, "Pubs, bars, clubs. None of it.", or in words core does not list. They were 92 before the checks were held to where the number or the thing stands, and not to the words a model quoted. Holding the guess to every sign of doubt in the whole sentence, in place of the words that turn in what leads up to the thing, brought the 92 to 67, and cost the careful stand-in 10 right readings and the measured model 7 of 85. So the floor rests on the model reading a turn rightly, and on the person who presses. The one model that was measured read one sentence of 113 backwards behind these checks.
- **What holding the checks to where a thing stands costs.** Three right readings of the careful stand-in are offered with no guess: "violence scares me", where core lists "scared" and not "scares", and "somewhere with history" twice, where no phrase of core's names an end of the scale. One budget is, "I can't pay more than £1,450", where core does not list the words among those that cap a number.
- **Neither stand-in quotes to deceive.** Each rests an edit on the words that name the thing, or on a whole sentence. What a model can do that chooses its words to get past a check is held in `services/api/tests/test_adversary.py`.
- **What is offered does not depend on what was sent.** No case of the 781 ends otherwise, for either stand-in.
- **A stand-in cannot say whether a real model reads less well with the words alone.**

Measured again on 2026-09-24, on the 820 cases the set now holds, before and after the guess was held to what is said about a thing (ADR 0012). By what a person would get who pressed every guess:

| Reader | Right | In part | Not read | Unasked guess | BACKWARDS GUESS | Never to be offered | Applied with no press | Readings of the rules lost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `right`, before | 401 | 48 | 126 | 1 | 0 | 0 | 0 | 3 |
| `right`, after | 399 | 49 | 127 | 1 | 0 | 0 | 0 | 3 |
| `backwards`, before | 221 | 51 | 175 | 46 | 89 | 0 | 0 | 4 |
| `backwards`, after | 232 | 54 | 182 | 41 | 73 | 0 | 0 | 4 |

- **What the two checks cost the careful stand-in.** Three cases lose their guess, each a wish of somebody of the speaker's own: `other-015`, `other-029` and `other-037`. The cases say a careful person would raise each, and the guard asks. `list-010` gains one.
- **What they close for the careless one.** Sixteen backwards guesses and five that nobody asked for: a word of dread after the thing, "pubs, yuck", and a wish of somebody else's, "my mum is after a park". What is left is a turn in another sentence, in the heading of a list, or in words core does not list.
- **A reading of the rules is lost on three cases, and on four for the careless stand-in**, before and after: `whole-001`, `whole-018` and `whole-035`, and `whole-008`. Each names a place the release does not hold, which the rules alone ask about. With a model on the question is asked only where the model reads the journey too. The cases were added after the first measurement of the stand-ins, and the loss is not of these checks' making.

## Read the answers on disk again

```
uv run python evals/reader/replay.py                # every answer, counted
uv run python evals/reader/replay.py --look 1 --show
```

One model, `gemini-3.5-flash-lite`, read 112 made-up sentences once each, as the service would ask it, and nine of them twice or four times more. What it answered is in `reader/answers/`, word for word, with the tokens each call used. 82 of the sentences are cases of this set, and 30 were written for the measurement and are in `reader/answers/cases/`. `replay.py` hands each answer back to the reader in a model's place, so that a change to the checks is measured on what a model has in fact answered, and nothing is paid for.

On the first look of each sentence, on 2026-09-24: 77 calls would be made, and 35 sentences are read by the rules with no call. 84 are right, 11 in part and 14 not read. Three hold a guess at a fair reading the case does not name. No backwards reading is marked as the guess: "my mum is after a park" was, until the guard read whose wish it is. Nothing is applied, nothing is offered that is never to be offered, and no reading of the rules is lost. The rules alone read 61 of them rightly.

That is a fit and not a measurement: the checks were chosen after reading these answers. `test_replay.py` holds the counts, so that a change that moves one is seen.

## Run it against the model-backed reader

One model has been measured once, on 112 sentences: see "Read the answers on disk again" above. The whole set has never been run against a provider. What follows is how it is meant to work, for Gemini, which comes first. `docs/design/models.md` has the other three, what the first call must settle, and how a key is handed over.

```
read -rs GEMINI_API_KEY && export GEMINI_API_KEY
export BURRO_MODEL_PROVIDER=gemini BURRO_MODEL_TIMEOUT_S=30
uv run python evals/reader/score.py --reader model --workers 4 --save evals/reader/baseline/gemini.json
```

The first line reads the key without showing or recording it. Close the shell afterwards.

- Each case is one call to the provider, and each call is paid for. See the next section.
- The sentence of each case is sent to the provider. The sentences are made up, so nothing private leaves.
- The reader is made as the service makes it, from the same settings: `BURRO_MODEL_PROVIDER`, the provider's key, `BURRO_MODEL_ID`, `BURRO_MODEL_TIMEOUT_S`, `BURRO_MODEL_MAX_TOKENS` and `BURRO_MODEL_SENDS_SETTINGS`. It asks nothing of the terms, because no person typed the sentences. It takes only a model the provider's adapter was fitted to.
- The words go alone, as in the service. To measure a provider sent the search settings as well, set `BURRO_MODEL_SENDS_SETTINGS=yes`, run again, and compare the two case by case with `--against`. The eight cases that start from a search that holds something are where a difference would show.
- A call that times out, is capped, or answers out of shape is counted as `failed`, and the rules do not answer in its place. The service waits 6 seconds. `BURRO_MODEL_TIMEOUT_S=30` measures reading apart from speed.
- If many cases fail as `ModelCapped`, lower `--workers`.
- A model does not answer the same way twice. Run it three times before you believe a difference of a few cases.
- A model is held to the floor of its provider. `floor.json` holds one for each of the four, and none has a limit yet, so the first run fails only if a case is reversed. Read the reversed and unasked sentences first. Then set the provider's floor a little under what you measured.
- Compare a provider with the rules case by case with `--against evals/reader/baseline/rule.json`.
- A reader that marks a guess is judged by what was offered as well, and held to the floor under "What was offered" above.

## What a run costs

The rule-based reader costs nothing, and nor does the stand-in.

For a model, `docs/design/models.md`, section 3, has what each provider charged on the day its page was read, for 1,000 searches of 3,000 tokens in and 300 out. For Gemini that was 1.65 US dollars, so one run of this set, 871 cases, is about 1.4 dollars and three runs about 4.

| Part of one call | Size | Tokens, about |
|---|---|---|
| The instructions | 10,900 characters | 2,700 |
| The shape the answer must take | 5,530 characters | 1,500 |
| The sentence | 600 characters at most | 150 |
| The search as it stands, where it is sent | 600 characters | 150 |
| The answer | six lists, mostly empty | 200 |

These are estimates. The tokens are worked out from characters, at four to a token. None was counted. The scorer prints the tokens a run used, so the first run replaces this table.

## What this does not measure

- **Whether the right area comes first.** It scores the edits, not the ranking. Ranking has tests of its own.
- **Follow-ups.** Eight cases start from a search that already holds something. The rest are first prompts.
- **How a real person types.** The sentences are one author's guess at it. Until there is consent to keep real prompts, that is all it can be.
- **The model-backed reader.** Not yet. See above.
- **Other languages, properly.** The plan puts them out of scope for v1. The cases are here so that a reader which meets one does no harm, and they were written without a native speaker's review.
