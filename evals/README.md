# evals

How well does Burro read what a person types? This folder answers that, for any reader, in under a second, with no model and no network.

Burro turns a sentence into typed edits to a search. Two readers sit behind one interface: the rules in `packages/core`, and a model in `services/api`. `evals/reader` holds made-up sentences, what a correct reading of each one is, and a scorer that runs a reader over all of them.

| Path | What it is |
|---|---|
| `reader/cases/*.jsonl` | The cases, one file for each kind of sentence. Written by hand |
| `reader/score.py` | The scorer. Standard library and `burro_core` only |
| `reader/floor.json` | The least a reader may score before a run fails |
| `reader/controls.py` | Two readers whose faults are known, to measure a real one against |
| `reader/model_reader.py` | Makes the model-backed reader as the service makes it. The only file here that imports the API |
| `reader/test_score.py` | Tests of the scorer itself |
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
3. more cases than `unasked_ceiling` hold an edit nobody asked for.

A run of part of the set, with `--group` or `--case`, is held to the first rule only.

## What the report says

Every case ends as one of these. The worst thing found decides.

| Outcome | What happened |
|---|---|
| **REVERSED** | The reader did the opposite of what was said. It raised what was turned down, added a journey to a place the person wants distance from, or made the other rule for an area. The sentences are always listed |
| unasked | The reader made an edit nobody asked for: a wish of someone else's, a number the words do not give, a workplace that is over. The sentences are always listed |
| declined | The reader read nothing of what was asked. The form is still on the screen, so this costs little |
| in part | The reader read some of what was asked, or gave a notice or asked a question that was not called for |
| correct | Everything asked for happened, and nothing else did |
| failed | The reader raised an error. Only a model-backed reader can |

Under the table are two more lines. Some cases ask for something, and some are right to leave alone: a question, a wish of someone else's, a sentence about the weather. A reader that does nothing is right about every case of the second kind, so one share for the whole set flatters it. The two lines give each kind its own share.

The scorer prints counts, case ids and sentences from the cases. It never prints what a reader answered, and of an error it keeps only the name of its class.

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
| `held` | Optional. What the search already holds, for a follow-up: `journeys`, `areas`, `weights`, `tags`, `budget` |

Anything `expect` does not name must stay as it was. A reader that moves it has made an edit nobody asked for.

**Features and tags.** Each is written `feature:<id>` or `tag:<id>`, with the ids of the contract's section 3.

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

## Run it against the model-backed reader

This has never been done. What follows is how it is meant to work.

```
export ANTHROPIC_API_KEY=...    # in your shell, and never in a file
uv run python evals/reader/score.py --reader claude --workers 8 \
    --save evals/reader/baseline/claude.json
```

- Each case is one call to the provider, and each call is paid for. See the next section.
- The sentence of each case is sent to the provider. The sentences are made up, so nothing private leaves.
- The reader is made as the service makes it, from the same settings: `BURRO_MODEL_ID`, `BURRO_MODEL_TIMEOUT_S`, `BURRO_MODEL_MAX_TOKENS`. The plan asks that every evaluation is also run on its second model: set `BURRO_MODEL_ID` and run again.
- A call that times out, is capped, or answers out of shape is counted as `failed`, and the rules do not answer in its place. The service waits 6 seconds. To measure reading apart from speed, set `BURRO_MODEL_TIMEOUT_S=30`.
- If many cases fail as `ModelCapped`, lower `--workers`.
- A model does not answer the same way twice. Run it three times before you believe a difference of a few cases.
- `floor.json` holds no floor for `claude` yet, so the first run fails only if a case is reversed. Read the reversed and unasked sentences first. Then set the floor a little under what you measured.
- Compare the two readers case by case with `--against evals/reader/baseline/rule.json`.

## What a run costs

The rule-based reader costs nothing.

For the model, the published price of the default model, `claude-haiku-4-5`, was 1 US dollar for a million tokens in and 5 dollars for a million out, read from the provider's [pricing page](https://platform.claude.com/docs/en/about-claude/pricing) on 2026-09-23.

| Part of one call | Size | Tokens, about |
|---|---|---|
| The instructions | 8,053 characters | 2,000 |
| The shape the answer must take | 5,530 characters | 1,500 |
| The sentence and the search as it stands | 600 characters | 170 |
| The answer | six lists, mostly empty | 200 |

| For 1,000 cases | Tokens | US dollars |
|---|---|---|
| In | 3.7 million | 3.70 |
| Out | 0.2 million | 1.00 |
| **All** | | **about 4.70** |

One run of this set, 655 cases, is about 3 dollars, and three runs about 9. A dearer model costs in proportion to its price.

These are estimates. The tokens are worked out from characters, at four to a token. None was counted. The scorer prints the tokens a run used, so the first run replaces this table.

Two things could make it cheaper, and neither is relied on here. The instructions are marked to be cached, and a cached token is a tenth of the price, but the provider caches nothing under a least length that depends on the model. If the scorer reports 0 tokens read from the cache, the instructions are under it. And the provider's batch service is half the price, but the reader calls the service a person would reach, one call at a time, and nothing here uses the batch service.

## What this does not measure

- **Whether the right area comes first.** It scores the edits, not the ranking. Ranking has tests of its own.
- **Follow-ups.** Eight cases start from a search that already holds something. The rest are first prompts.
- **How a real person types.** The sentences are one author's guess at it. Until there is consent to keep real prompts, that is all it can be.
- **The model-backed reader.** Not yet. See above.
- **Other languages, properly.** The plan puts them out of scope for v1. The cases are here so that a reader which meets one does no harm, and they were written without a native speaker's review.
