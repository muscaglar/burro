# Baseline: the rule-based reader

Measured on 2026-09-23 at 16:16 local time, on the synthetic release, with no model and no network.

| What | Value |
|---|---|
| Reader | `RuleInterpreter` in `packages/core/src/burro_core/interpret.py` |
| Engine version | 1.3.0 |
| Catalogue version | 1 |
| Reader files | `b831d2811a82`: the first 12 characters of one SHA-256 over `interpret.py`, `vocabulary.py`, `places.py`, `reducer.py` |
| Release | `syn-2026-09-23-01` |
| Cases | 655 |
| Floor | correct share 0.48, at most 2 unasked, none reversed |
| Result | PASS |

**The reader was being changed while this was measured.** `interpret.py` and `vocabulary.py` changed several times in the hour this set was built, and the engine version moved from 1.2.0 to 1.3.0 between two runs a few minutes apart. The reader was in no commit, so the hash above is the only name this measurement has. The numbers here are for the files with that hash and for no others. The scorer prints the hash at the top of every run. To see what has moved since:

```
uv run python evals/reader/score.py --against evals/reader/baseline/rule.json
```

## The result

| group | cases | correct | in part | declined | unasked | REVERSED | correct share |
|---|---:|---:|---:|---:|---:|---:|---:|
| plain wishes | 60 | 33 | 0 | 27 | 0 | 0 | 55% |
| budgets | 44 | 17 | 0 | 26 | 1 | 0 | 39% |
| journeys | 45 | 26 | 1 | 18 | 0 | 0 | 58% |
| negatives | 73 | 40 | 2 | 31 | 0 | 0 | 55% |
| double negatives | 36 | 14 | 0 | 22 | 0 | 0 | 39% |
| typos | 44 | 8 | 0 | 35 | 1 | 0 | 18% |
| lists | 40 | 12 | 3 | 25 | 0 | 0 | 30% |
| questions | 40 | 25 | 0 | 15 | 0 | 0 | 62% |
| other peoples wishes | 41 | 28 | 0 | 13 | 0 | 0 | 68% |
| who lives there | 50 | 38 | 2 | 10 | 0 | 0 | 76% |
| crime | 34 | 19 | 1 | 14 | 0 | 0 | 56% |
| off topic | 35 | 13 | 0 | 22 | 0 | 0 | 37% |
| other languages | 40 | 2 | 0 | 38 | 0 | 0 | 5% |
| very long | 28 | 0 | 9 | 19 | 0 | 0 | 0% |
| very short | 45 | 42 | 0 | 3 | 0 | 0 | 93% |
| all | 655 | 317 | 18 | 318 | 2 | 0 | 48% |

488 cases ask for something: 151 correct (31%)

167 cases are right to leave alone: 166 correct (99%)

Read from the top: 0 reversed, 2 with an edit nobody asked for, and 48% read correctly.

The groups it reads best are very short (42 of 45), who lives there (38 of 50), other peoples wishes (28 of 41). The groups it reads least are very long (0 of 28), other languages (2 of 40), typos (8 of 44), lists (12 of 40).

## Against the two controls

| Reader | What it does | Correct | In part | Declined | Unasked | REVERSED | Asked for, and read | Right to leave, and left |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `nothing` | Reads nothing | 167 | 0 | 488 | 0 | 0 | 0 of 488 | 167 of 167 |
| `keywords` | Raises whatever is named | 200 | 33 | 179 | 105 | 138 | 115 of 488 | 85 of 167 |
| `rule` | The rule-based reader | 317 | 18 | 318 | 2 | 0 | 151 of 488 | 166 of 167 |

`nothing` is the score to beat: it is right wherever the right thing is to leave the search alone, and nowhere else. `keywords` is what the cases are there to catch. The two are in `controls.py`.

## Reversed

None.

## Edits nobody asked for

| Case | Sentence | What it did |
|---|---|---|
| `budget-037` | £1,100 to £1,300 for a studio or one bed | the budget is not the amount the words give |
| `typo-021` | I study at wexmoor uni | a journey to Wexmoor University was to be held: not added; a journey to Wexmoor was added |

## A notice given without cause

The neutral notice says that Burro ranks places and never residents. It was given for these sentences, which ask nothing about who lives anywhere. Most name a campus as a place of work or study. A person who says they work at a university is told that Burro does not rank by who lives somewhere.

| Case | Sentence | What it did |
|---|---|---|
| `crime-010` | I study crime at university | the notice neutral_places was given, and none was called for |
| `journey-011` | two of us: I work at Cindermoor Works and my partner works at Wexmoor University | the notice neutral_places was given, and none was called for |
| `journey-025` | no further than 20 minutes from Wexmoor University on foot | the notice neutral_places was given, and none was called for |
| `journey-044` | Wexmoor University is where I work, and I'd like a park | the notice neutral_places was given, and none was called for |
| `other-011` | My partner works at Wexmoor University | the notice neutral_places was given, and none was called for |
| `long-001` | Hi, so me and my partner are moving down in January for work. I'll be at Cindermoor Works and she's at Wexm... | the notice neutral_places was given, and none was called for |
| `long-006` | ok so basically i need somewhere cheap-ish, like 900 a month for a room in a shared house, and it has to be... | the notice neutral_places was given, and none was called for |
| `long-009` | Looking for a flatshare with two friends, so three bedrooms, up to £3,000 between us. One of us works at Go... | the notice neutral_places was given, and none was called for |
| `long-017` | Three things matter and nothing else does. One, I have to be able to get to Wexmoor University in 30 minute... | the notice neutral_places was given, and none was called for |
| `who-020` | a diverse range of restaurants | the notice neutral_places was given, and none was called for |
| `who-021` | I am a student nurse looking for a quiet flat near Pellam Infirmary | the notice neutral_places was given, and none was called for |
| `who-046` | I teach at Wexmoor University and want to walk to work | the notice neutral_places was given, and none was called for |

## A question asked without cause

None.

## What it did not read

318 cases were declined and 18 were read in part. In each the reader made no edit, or fewer than were asked for. None of them changed a search against what was said. To list them:

```
uv run python evals/reader/score.py --show declined --show partial
```

## Reproduce it

```
uv run python evals/reader/score.py
uv run python evals/reader/score.py --reader nothing
uv run python evals/reader/score.py --reader keywords
uv run python evals/reader/score.py --save evals/reader/baseline/rule.json
```

The last line writes the outcome of every case to `baseline/rule.json`. Write it again, and this file with it, whenever the floor is moved.
