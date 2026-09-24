# Baseline: the rule-based reader

Measured on 2026-09-24, on the synthetic release, with no model and no network, after the reader was taught the whole of a search as a newcomer types one, and after a check of that work mended three faults in it.

| What | Value |
|---|---|
| Reader | `RuleInterpreter` in `packages/core/src/burro_core/interpret.py`, which applies a prompt only when the whole of it is plain (contract 8.2, ADR 0012 as amended) |
| Engine version | 1.10.0 |
| Catalogue version | 5 |
| Reader files | `f5702b8ffe4e`: the first 12 characters of one SHA-256 over `interpret.py`, `grammar.py`, `reading.py`, `lexicon.py`, `vocabulary.py`, `places.py`, `reducer.py` |
| Release | `syn-2026-09-23-01`, with gritty built as a scale (variant `b`) |
| Cases | 819 |
| Floor | correct share 0.52, none unasked, every plain prompt correct, none reversed |
| Result | PASS |

The scorer prints the hash at the top of every run. To see what has moved since:

```
uv run python evals/reader/score.py --against evals/reader/baseline/rule.json
```

## The result

| group | cases | correct | suggested | in part | declined | unasked | REVERSED | correct share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| plain wishes | 64 | 36 | 25 | 0 | 3 | 0 | 0 | 56% |
| budgets | 44 | 21 | 9 | 0 | 14 | 0 | 0 | 48% |
| journeys | 51 | 36 | 7 | 1 | 7 | 0 | 0 | 71% |
| negatives | 85 | 45 | 40 | 0 | 0 | 0 | 0 | 53% |
| double negatives | 36 | 14 | 18 | 0 | 4 | 0 | 0 | 39% |
| typos | 44 | 8 | 23 | 0 | 13 | 0 | 0 | 18% |
| lists | 40 | 8 | 32 | 0 | 0 | 0 | 0 | 20% |
| questions | 40 | 25 | 15 | 0 | 0 | 0 | 0 | 62% |
| other peoples wishes | 41 | 28 | 10 | 0 | 3 | 0 | 0 | 68% |
| who lives there | 54 | 42 | 2 | 1 | 9 | 0 | 0 | 78% |
| crime | 41 | 26 | 10 | 0 | 5 | 0 | 0 | 63% |
| off topic | 35 | 13 | 0 | 0 | 22 | 0 | 0 | 37% |
| other languages | 40 | 2 | 10 | 0 | 28 | 0 | 0 | 5% |
| very long | 28 | 0 | 8 | 2 | 18 | 0 | 0 | 0% |
| very short | 45 | 42 | 1 | 0 | 2 | 0 | 0 | 93% |
| plain prompts | 31 | 31 | 0 | 0 | 0 | 0 | 0 | 100% |
| suggestions | 29 | 11 | 18 | 0 | 0 | 0 | 0 | 38% |
| vibes | 37 | 25 | 7 | 1 | 4 | 0 | 0 | 68% |
| whole searches | 34 | 14 | 16 | 0 | 4 | 0 | 0 | 41% |
| all | 819 | 427 | 251 | 5 | 136 | 0 | 0 | 52% |

625 cases ask for something: 233 correct (37%), 484 read or offered (77%)

194 cases are right to leave alone: 194 correct (100%)

Offered where nothing was asked: 140

65 cases are plain and must be applied: 65 correct (100%)

**Of the 625 prompts that ask for something, 238 are applied, 251 become suggestions and 136 are declined.** Applied is 233 read correctly and 5 read in part.

Read from the top: 0 reversed, 0 with an edit nobody asked for, 52% read correctly, and 31% more offered for the person to choose.

The groups it reads best are plain prompts (31 of 31), very short (42 of 45), who lives there (42 of 54). The groups it reads least are very long (0 of 28), other languages (2 of 40), typos (8 of 44), lists (8 of 40). A list with a heading, a long story and a typo are seldom plain, so they are offered or declined. That is what a model is for.

## Against the measurement before it

The measurement before this one was of the reader at engine 1.5.0, reader `d1eff93e9fcf`, on 781 cases. No case then held the whole of a search in a few sentences: a few hedged wishes, a word for a smart area, a word for character, a journey given as a range of minutes to a place the release does not hold, and a home to buy. Of such a search the reader offered about half of the parts and made nothing of the rest. 31 cases were written, of a whole search and of each part of one alone, before the reader was changed. They are the group `whole_searches`, and every sentence in it is made up.

| | Before, on its 781 cases | Before, on the 812 | Now, on the same 781 | Now, on all 819 |
|---|---:|---:|---:|---:|
| Correct | 408 | 412 | 409 | 427 |
| Suggested | 232 | 236 | 235 | 251 |
| In part | 5 | 5 | 5 | 5 |
| Declined | 136 | 159 | 132 | 136 |
| Unasked | 0 | 0 | 0 | 0 |
| Reversed | 0 | 0 | 0 | 0 |

**On the 31 new cases the reader as it was read 4, offered 4 and declined 23, and left 10 of the 12 plain ones unapplied.** The run failed on the share read correctly, 0.507, and on the plain prompts. It was scored from a copy of the reader as it stood when the cases were written, with the new cases beside it.

| What was not read | Cases | As it was | Now |
|---|---|---|---|
| A range of minutes: "35-40min", "30 to 40 minutes" | `whole-006`, `whole-009`, `whole-011`, `whole-013`, `whole-014`, `whole-019` | Not plain, and the minutes unread | Read as the longer of the two, and marked as assumed |
| A commute from a place, and minutes from work at one | `whole-013`, `whole-015`, `whole-016` | Offered as a rule for an area, or unread | A journey to the place, where a time is said of it or it is where the speaker works. A place that is commuted from with no time said of it is offered as a journey, and never applied |
| A place the release does not hold | `whole-001`, `whole-017`, `whole-018` | Unread in a prompt that is not plain | Asked about, plain or not |
| The size and the kind of a home | `whole-001`, `whole-020`, `whole-021`, `budget-030` | Offered only where it moved the search, and unread where the search could not hold it | Offered whenever it is named, with what cannot be held said beside it |
| Millions as "m" | `whole-022`, `budget-016` | Unread | Read where the sentence says what the amount is for. Offered, or unread, where it does not |
| A word for a smart area: "affluent", "posh", "upmarket" | `whole-023`, `who-047` | Unread | Offered towards Polished, as of the place |
| A word for character: "identity", "its own feel", "soulless" | `whole-024` to `whole-026`, `long-013` | Unread | Offered three ways |
| "Up and coming" | `whole-027` | Heard as what Burro has no measure of | Offered as the ends of the scale, which says what it counts |
| "Access to", "around it", "but with" | `whole-029`, `whole-001` | Not plain | Plain |

On the 781 cases of the last measurement none is worse and four are better: `budget-016`, `budget-030`, `long-013` and `who-047`. **One case was changed.** `who-047`, "somewhere posh", held the word to be a wish about residents and asked for the neutral notice. It was decided on 2026-09-24 that a word for a smart area is read as of the place, so the case now holds it to be offered towards Polished.

Four of the new cases are still declined: `whole-002`, `whole-004`, `whole-010` and `whole-012`. Each gives the minutes of its journey in words the grammar does not make, "30 to 40 minutes door to door is fine", so the journey is offered without them. That is what a model is for.

**A check of the reader found three faults in what it had been taught, and seven cases were written for them.** Each is made up.

| What was wrong | Cases | As it was | Now |
|---|---|---|---|
| A number of "m" under a word that caps: "near the tube, 5m max" | `whole-032`, `whole-033` | REVERSED: applied as a budget of millions of pounds, to buy | Nothing is applied. What was named beside it is offered |
| A place that is commuted from, beside the place the person works at | `whole-034`, `whole-015` | REVERSED: a journey was added to the home the person is leaving. Alone, "I commute from" was applied | Offered as a journey, for the person to choose |
| A word for a smart area or for character, said of people: "posh locals", "a Polish identity" | `who-051` to `who-054` | Declined: the scale or the three readings of character were offered, and no notice was given | The neutral notice, and no offer |

`whole-015` was read correctly and is now offered, which is the one case of the 812 that ends lower. No other case moved.

The floor did not move. The share read correctly is 0.521 against a floor of 0.52.

## Against the two controls

| Reader | What it does | Correct | Suggested | In part | Declined | Unasked | REVERSED | Asked for, and read | Right to leave, and left |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `nothing` | Reads nothing | 194 | 0 | 0 | 625 | 0 | 0 | 0 of 625 | 194 of 194 |
| `keywords` | Raises whatever is named | 219 | 0 | 49 | 204 | 168 | 179 | 134 of 625 | 85 of 194 |
| `rule` | The rule-based reader | 427 | 251 | 5 | 136 | 0 | 0 | 233 of 625 | 194 of 194 |

`nothing` is the score to beat: it is right wherever the right thing is to leave the search alone, and nowhere else. `keywords` is what the cases are there to catch. The two are in `controls.py`.

## Reversed

None.

## Edits nobody asked for

None.

## A notice given without cause

The neutral notice says that Burro ranks places and never residents. It was given for these sentences, which ask nothing about who lives anywhere. Most name a campus in a prompt that is not plain, where a campus may be what the person wants distance from. A person who says their partner works at a university is told that Burro does not rank by who lives somewhere.

| Case | Sentence | What it did |
|---|---|---|
| `journey-011` | two of us: I work at Cindermoor Works and my partner works at Wexmoor University | the notice neutral_places was given, and none was called for |
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

136 cases were declined and 5 were read in part. In each the reader made no edit, or fewer than were asked for, and did not offer all that was asked. None of them changed a search against what was said. To list them:

```
uv run python evals/reader/score.py --show declined --show partial --show suggested
```

## Reproduce it

```
uv run python evals/reader/score.py
uv run python evals/reader/score.py --reader nothing
uv run python evals/reader/score.py --reader keywords
uv run python evals/reader/score.py --save evals/reader/baseline/rule.json
```

The last line writes the outcome of every case to `baseline/rule.json`. Write it again, and this file with it, whenever the floor is moved.
