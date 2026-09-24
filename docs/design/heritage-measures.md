# Conservation cover and listed buildings: what core and the website must change

Status: a proposal, written 2026-09-24. Two measures are built in the pipeline. Nothing of core, of the contract, of the API or of the website was changed for them. This page says what each must change, file by file and test by test, so that it can be made in one change that a person reads. It is not legal advice, and no lawyer has read it.

What was read and counted is in [docs/research/data/heritage.md](../research/data/heritage.md). Both measures say something of land and buildings. Neither says anything of who lives anywhere.

## 0. In short

| Question | Answer |
|---|---|
| Does core have to change for a build to carry the two | No. Each is named and measured as core's catalogue says |
| What does a build now carry | Ten measures. Built age gains a band for 979 of 1,002 areas |
| What must change before Built age is shown | Three things, in section 2: the credit, the low end of the scale, and what is said beside each figure |
| What is the founder's to decide | Five things, in section 4 |

## 1. What a build carries, as core stands

| Feature | Core's name | Core's unit | What the pipeline works out | Same as core |
|---|---|---|---|---|
| `conservation_cover` | Share of the area in a conservation area | % | The land inside a conservation area over all the land of the area, times 100 | Yes |
| `listed_buildings` | Listed buildings | per km² | The entries of the national list in the area, over its land in square kilometres | Yes |

| Vibe | Recipe in core | Held by a build | In 100 | Placed |
|---|---|---|---|---|
| Built age | 35 `homes_pre1919`, 25 `conservation_cover`, 20 `listed_buildings`, 20 `homes_post2000` low | The first three | 80 | 979 areas |
| Village feel | 25 `independents_nearby`, 20 `centre_small`, 20 `centre_compact`, 20 `homes_pre1919`, 15 `conservation_cover` | The last two | 35 | None |

The licence registry asks that conservation areas never decide a tag alone. Core's rule of 60 in 100 keeps that: conservation cover is 25 in 100 of one recipe and 15 of the other. `tests/derive/test_conservation_cover.py` holds every recipe of core to it.

Likeness now counts six measures, of which these are two. Core marks both `in_likeness`.

## 2. What must change, and where

### 2.1 The credit holds a date that nothing fills in

The publisher's statement says "was obtained on [date]". A release carries the credit as the registry writes it, with the day beside it as `retrieved_on`. Nothing puts the day into the sentence. The credits of the statistics office hold `[year]` in the same way.

| Where | What changes | Test |
|---|---|---|
| `packages/pipeline/src/burro_pipeline/assemble/release.py`, `sources_of` | Write `[date]` as the day the file was retrieved, and `[year]` as its year, in the credit of each source | `tests/assemble/test_preview.py`: a new test that no credit of a release holds a square bracket |
| `packages/pipeline/src/burro_pipeline/evidence/served.py`, `_of_the_credits` | Hold a credit to the registry's with the same two words filled in, from the receipts in the evidence | `tests/evidence/test_served.py`: the test of `credit_is_the_registrys` gains a credit with a date, right and wrong |
| `apps/web/src/components/SourceList/SourceList.tsx` | Nothing, once the release carries the filled credit. It prints what it is given | `SourceList.test.tsx`: no credit on the page holds `[` |
| `apps/ios`, the list of sources | The same | Its own test of the list |

It is left to one change because it moves the credit of every source, and the hash of every release.

### 2.2 The low end of Built age is named for what is not yet measured

The scale runs from Newer to Historic. Its low end rests on `homes_post2000`, which no build carries yet. On the three parts held, the lowest band is the areas with few old homes, little protected land and few listed buildings. They hold no more new homes than London does.

| Where | What changes | Test |
|---|---|---|
| `packages/core/src/burro_core/lexicon.py`, the two lines that read "new build", "new builds" and "modern flats" as Built age toward its low end | While a release carries no `homes_post2000`, read them as a wish for `homes_post2000`, which the release then says it cannot meet. Read them as Built age toward Newer once the release carries all four parts | `packages/core/tests/`: the test of the lexicon gains a release with three parts and one with four |
| `packages/core/src/burro_core/catalogue.py`, `TagId.BUILT_AGE` | Nothing in the recipe | None |
| `evals/reader/cases/` | A case for "new build flats" on a release with three parts: nothing is ranked toward the low end | The score of the reader |

Whether Built age is served at all on three parts is question 4.

### 2.3 What a figure cannot see is not served

Each measure writes one or two sentences of what it cannot see. They reach `build.json`, beside the release. No release holds them, so no page can show them beside the figure. This is so of every measure, and not of these two alone.

| Where | What changes | Test |
|---|---|---|
| `packages/core/src/burro_core/release.py`, `Metric` | A field `cannot_see`, a list of sentences. It is the build's to say, as `definition` is | `packages/core/tests/`: a release whose metric holds none is refused |
| `packages/pipeline/src/burro_pipeline/derive/catalogue_row.py` | Takes the sentences from the measure | `tests/derive/test_catalogue_row.py` |
| `contracts/openapi.json`, by `make openapi` | The field, on a feature of `/v1/meta` | The test that the contract is not stale |
| `apps/web`, the area page and the methods page | The sentences under the figure, as a vibe's are | The page's own tests, on answers recorded again |
| `docs/design/contract.md`, section 2 | The field, and that it is never empty | |

The sentences, as the pipeline holds them:

| Measure | What it cannot see |
|---|---|
| `conservation_cover` | It counts the land inside a line a planning authority drew, so it cannot see what the buildings inside the line are like, how old they are or what state they are in, and a street of old houses outside any line counts for nothing |
| | The publisher says the data may be incomplete, so where an authority sent only some of its conservation areas the figure is too low, and where it sent none there is no figure |
| `listed_buildings` | It counts entries on the national list, and an entry may be one house, a whole terrace, a church, a bollard or a milestone, so it cannot see how many buildings are protected or how much of a street they make up |
| | Every entry counts the same whatever its grade, so it cannot see how much a building matters, and it cannot see a building that is old and not listed, or the state a building is in |

### 2.4 The contract names no source for listed buildings

| Where | What changes |
|---|---|
| `docs/design/contract.md`, the row of `listed_buildings` in section 2 | The source, which the row gives as "none named yet": `historic-england-listed-buildings` |
| `docs/design/london-data-sources.md`, the rows of the two sources | Each gives a reading that was not built. Conservation cover is a share of land, and not of homes. Listed buildings are for each square kilometre, and not for each 1,000 homes. The credit is no longer shorter than the page's |

## 3. What is proposed for each vibe

| Vibe | Proposal | Why |
|---|---|---|
| Built age | Keep the recipe. Do not show the vibe until `homes_post2000` is carried, or show it with its low end unnamed | On three parts its low end is "not historic", and its name says "Newer" |
| Built age | Count listed buildings for each square kilometre, as core has it | For each 1,000 homes puts first the places with few homes, for that reason alone |
| Built age | Do not weigh an entry by its grade | Nine entries in ten are of grade II, and 583 of 1,002 areas hold no entry of a higher grade. A weight would be Burro's opinion of what a grade is worth, and the list gives none |
| Village feel | No change. It stays unplaced | It holds 35 in 100. What makes a place a village is a centre of its own, which three parts that are not built measure |
| Likeness | Count one of the two, and not both | The two agree with one another more than either agrees with anything else. Counting both counts protected heritage twice |

## 4. What is the founder's to decide

| # | Question | Recommended |
|---|---|---|
| 1 | May Built age be served on three of its four parts | Not under the name "Newer" for its low end. Wait for the fourth part, which rests on a file already held |
| 2 | Is "Listed buildings" the right name for a count of entries | Keep the name. Say what an entry is beside the figure, which needs 2.3 |
| 3 | For each square kilometre, or for each 1,000 homes | For each square kilometre. It is a figure of the place, and it is what core names |
| 4 | Should likeness count both measures | One. Conservation cover, which has a figure for more kinds of place |
| 5 | Is a person to hold each authority's count of conservation areas against the authority's own page before the figure is shown | Yes, for the 14 authorities that rest wholly on records the file marks `some`. 156 of the 262 areas at nought are in them |

## 5. What was not built, and why

| What | Why |
|---|---|
| The credit with its date filled in | It moves the credit of every source and the hash of every release. Section 2.1 |
| The names of conservation areas on "Go and look" | The source is registered for `scoring`, and a name is `display`. The name of a record is never read |
| A figure for a kind of listed building, as a theatre or a church | The file has no field for the kind. The name would have to be read, and it never is |
| A weight for grade | Section 3 |
| A filter on any of this | None was asked for |
