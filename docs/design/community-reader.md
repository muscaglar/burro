# A community, reached through what is there: what the reader must do

Status: proposed, 2026-09-24. Nothing here is built in core, in the API or on the website. This page is what whoever joins the branches needs in order to make the change in one reviewed piece. It follows the founder's decision of 24 September 2026: ethnicity and religion are shown on an area's page and never ranked on, and a person reaches a community through what is there, such as a place of worship, a cultural centre or a food shop.

What is counted is in [the page on the measures](../research/data/community-places.md). This page is about words.

## 0. In short

| Question | Answer |
|---|---|
| What happens today to "near a mosque" | It is heard, filed under `community_amenities`, and answered with nothing |
| What happens today to "close to a Hindu temple" | The person is told that Burro does not rank by who lives somewhere. The reader takes the word before "temple" for a word about people. It is a fault |
| What should happen | A place of worship that is named as a building is offered: "A mosque nearby". The person chooses. Nothing is applied for them |
| What never happens | No offer of fewer, of further or of none. No offer from a word about people. No figure of who lives anywhere |
| What keeps the notice | Every sentence about people: "a Muslim area", "lots of Jewish families". And every wish to be kept from a building: "not many churches" |
| What is needed first | Nine features in core, each with one direction. Seven are weighed on request only and stand in no vibe |
| What is the founder's | Section 8 |

## 1. The rule

One question decides every sentence: **is the person asking for a building, or for people?**

| The words name | Example | What the reader gives |
|---|---|---|
| A building, wanted near | "near a mosque" | An offer of that building nearby. Nothing is applied until the person chooses it |
| A building, by a word for a belief and a word for a building | "a Hindu temple", "a Catholic church" | The same. The two words together are the name of a building |
| People | "a Muslim area", "lots of Jewish families" | No edit and no offer. The notice, in its fixed words |
| A building, not wanted | "not many churches", "away from mosques" | No edit and no offer. The notice. To be kept from a building is a request about who lives somewhere, as it is for a campus |
| Both | "a Jewish community with a synagogue nearby" | The notice for the people. An offer for the building |

Four rules follow.

1. **An offer is never applied by itself.** A place of worship is offered where a campus is applied. There are two reasons. What a person weighs says something of what they believe, so they should choose it knowingly. And the count rests on a file that nobody has held to a register, so the offer must say what it counts before it is chosen.
2. **An offer has one direction.** The choices are to add it and to ignore it. Where a search holds it already, the choices are to take it off and to leave it. There is no slider toward fewer.
3. **An offer says what it is.** Every offer carries the same note: "It counts buildings that one file lists within 800 metres of home, in a straight line. It says nothing of who lives near them."
4. **No word is turned into another.** "Muslim" is never read as a mosque. "A Jewish area" offers no synagogue. A person who wants the building says the building.

## 2. What is offered

Each is a count of buildings within 800 metres of home, in a straight line. The ids are the ones the rows of evidence are written under.

| Offer | Feature | Weighed | In a vibe | In likeness |
|---|---|---|---|---|
| A place of worship nearby | `worship_places` | On request | No | No |
| A church nearby | `worship_churches` | On request | No | No |
| A mosque nearby | `worship_mosques` | On request | No | No |
| A synagogue nearby | `worship_synagogues` | On request | No | No |
| A Hindu temple nearby | `worship_hindu_temples` | On request | No | No |
| A gurdwara nearby | `worship_gurdwaras` | On request | No | No |
| A Buddhist temple nearby | `worship_buddhist_temples` | On request | No | No |
| A cultural centre nearby | `cultural_centres` | On request | No | No |
| A community centre nearby | `community_centres` | As an amenity | It may be one kind of place to meet | No |

## 3. The words

| Words | Read as |
|---|---|
| church, churches, chapel, cathedral | A church nearby |
| mosque, mosques, masjid | A mosque nearby |
| synagogue, synagogues, shul | A synagogue nearby |
| Hindu temple, mandir | A Hindu temple nearby |
| gurdwara, gurdwaras, Sikh temple | A gurdwara nearby |
| Buddhist temple | A Buddhist temple nearby |
| temple, temples, with no word before | Two offers: a Hindu temple nearby, and a Buddhist temple nearby. The reader chooses neither |
| place of worship, places of worship | A place of worship nearby |
| cultural centre | A cultural centre nearby. The note adds: "Burro cannot tell whose a cultural centre is." |
| community centre, community hall | A community centre nearby |
| A word for a belief, then a word for a building of another | "a Muslim church": nothing is offered. The words are reported as unread |
| A word for a denomination, then church | "a Catholic church", "a Methodist chapel": a church nearby. The note adds: "Burro does not tell one church from another." |
| A word for a belief or for a country, then a cultural centre | "a Polish cultural centre": a cultural centre nearby, and `community_amenities` is reported as unmet for the word before it |
| A word for a belief, then school | "a church school", "a Catholic school", "Muslim schools": no offer of a place of worship and no offer of a school. `community_amenities` is reported as unmet. Schools are counted without regard to faith |
| kosher, halal, then a shop or a place to eat | No offer. `community_amenities` is reported as unmet, as today. Section 8 |

## 4. Thirty sentences

"Today" is what the reader of rules gave on 2026-09-24, asked through the API with no model. Every sentence is made up.

An offer is a row of `suggestions`. "Notice" is the status `policy_redirect` with the fixed words of contract 8.4. "Unmet" is `community_amenities` in `unmet`.

### 4.1 A building: an offer

| # | Sentence | Today | Should give |
|---|---|---|---|
| 1 | near a mosque | Unmet. Nothing else | Offer: a mosque nearby |
| 2 | walking distance to a synagogue | Unmet | Offer: a synagogue nearby |
| 3 | a gurdwara close by | Unmet | Offer: a gurdwara nearby |
| 4 | somewhere with a church nearby | Unmet | Offer: a church nearby |
| 5 | close to a Hindu temple | **Notice.** It is read as a request about people | Offer: a Hindu temple nearby. No notice |
| 6 | near a Buddhist temple | **Notice** | Offer: a Buddhist temple nearby. No notice |
| 7 | a Sikh temple nearby | **Notice** | Offer: a gurdwara nearby. No notice |
| 8 | near a Catholic church | **Notice** | Offer: a church nearby, with the note that Burro does not tell one church from another. No notice |
| 9 | a place of worship within a walk | Unmet | Offer: a place of worship nearby |
| 10 | near a temple | Unmet | Two offers: a Hindu temple nearby, a Buddhist temple nearby |
| 11 | near a mandir | Not read | Offer: a Hindu temple nearby |
| 12 | near a masjid | Not read | Offer: a mosque nearby |
| 13 | churches | Not read | Offer: a church nearby |
| 14 | quiet, leafy and near a mosque | Quiet streets and Leafy are applied. Unmet | Nothing is applied. Three offers: Quiet streets, Leafy, a mosque nearby |
| 15 | a lively area with a synagogue in walking distance | Pace is applied, toward Buzzy. Unmet | Nothing is applied. Two offers: Pace toward Buzzy, a synagogue nearby |
| 16 | I am Muslim and want a mosque close by | Unmet. "I am Muslim" is not read | Offer: a mosque nearby. "I am Muslim" says who is asking and asks for no one: no notice, and nothing is made of it |
| 17 | a cultural centre nearby | Offer: more culture nearby | Offer: a cultural centre nearby |
| 18 | a community centre nearby | Offer: Village feel | Offer: a community centre nearby |
| 19 | a Polish cultural centre | Unmet | Offer: a cultural centre nearby, with the note that Burro cannot tell whose it is. Unmet, for the word before it |

### 4.2 People: the notice

| # | Sentence | Today | Should give |
|---|---|---|---|
| 20 | a Muslim area | Notice | Notice. No offer of a mosque |
| 21 | lots of Jewish families | Notice | Notice. No offer of a synagogue |
| 22 | a Sikh community | Notice | Notice. No offer of a gurdwara |
| 23 | where Hindus live | Notice | Notice. No offer |
| 24 | a Christian neighbourhood | Notice | Notice. No offer |

### 4.3 A building, not wanted: the notice

| # | Sentence | Today | Should give |
|---|---|---|---|
| 25 | not many churches | Not read. **No notice** | Notice. No offer, and no edit toward fewer |
| 26 | away from mosques | Not read. **No notice** | Notice. No offer |
| 27 | no temples nearby | Not read. **No notice** | Notice. No offer |
| 28 | fewer churches | Not read. **No notice** | Notice. No offer |

### 4.4 Both, and what stands beside

| # | Sentence | Today | Should give |
|---|---|---|---|
| 29 | a strong Jewish community with a synagogue nearby | Notice. Unmet | Notice, for the community. Offer: a synagogue nearby |
| 30 | near a mosque but not a Muslim area | Notice. Unmet | Notice, for the area. Offer: a mosque nearby. The wish about the area is never applied, in either direction |

Four more, which the change must leave as they are or put right:

| Sentence | Today | Should give |
|---|---|---|
| a church school nearby | School results are weighed, as assumed. Unmet | Unmet alone. No weight on results: the words name a kind of school and not its results. No offer of a church |
| halal butchers nearby | Unmet | Unmet, as today |
| Turkish restaurants nearby | Places to eat and drink are weighed | The same, as today. The word for the cooking is not read |
| a diverse area with lots of places of worship | Notice. Unmet | Notice, for "diverse". Offer: a place of worship nearby |

## 5. What must change in core

Core is not changed on this branch. Each row is a change to make, with the test that holds it.

### 5.1 `ids.py`

| Change | Detail |
|---|---|
| Nine values of `FeatureId` | `worship_places`, `worship_churches`, `worship_mosques`, `worship_synagogues`, `worship_hindu_temples`, `worship_gurdwaras`, `worship_buddhist_temples`, `cultural_centres`, `community_centres` |
| `UnmetCategory.COMMUNITY_AMENITIES` | It stays. It no longer covers a place of worship. It covers a shop, a place to eat, a venue or a school of one community |

### 5.2 `catalogue.py`

| Change | Detail |
|---|---|
| Nine features | Label and short label as `Proposed` gives them in `derive/worship_nearby.py` and `derive/centres_nearby.py`. Unit `count`. Polarity `more`. `describes` is `buildings`. Native resolution `point`. `higher` is "more" and `lower` is "fewer": the two fill the sentence that says where an area stands among the others, and neither is a choice |
| Kind | `on_request` for the seven of worship and for cultural centres. `amenity` for community centres |
| `in_likeness` | False for all nine. How like two areas are is never counted on a place of worship |
| Family | None for the eight that are on request, as for crime. They are shown in no group of settings until they are asked for |
| `CATALOGUE_VERSION` | 6 |
| No recipe changes | `checked_recipe` already refuses a part that is weighed on request only |

### 5.3 `lexicon.py`

| Change | Detail |
|---|---|
| Phrases of section 3 | Each is a phrase of `LEXICON` with a feature and a `note`. A phrase with a note is never applied: the prompt is not plain, and the thing is offered with its note. It is the rule that "safe" and "gym" follow today. A suggestion that holds a note is chosen by its own label, and never with others at once |
| The note | One constant, used by every phrase of worship: the words of rule 3 of section 1. Two more for a church by denomination and for a cultural centre |
| `NO_MEASURE[COMMUNITY_AMENITIES]` | Loses "mosque", "church", "synagogue", "temple", "gurdwara", "place of worship" and "places of worship". Keeps "kosher", "halal" and what is sold |
| A word for a building of worship | A new tuple, `_WORSHIP`: the nouns of section 3. It is for `reading.py` |
| `_AMENITIES` | Gains no word of worship. A word there is read as a community's amenity with no feature, which a place of worship no longer is |
| `POLICY_LEXICON` | Unchanged. It holds words for people and never for buildings |

### 5.4 `reading.py`

| Change | Detail |
|---|---|
| `people_in` | A word that is only a word for a group, followed by a word of `_WORSHIP`, marks nothing. The two are left to the lexicon, which reads them as a building. Today "Hindu temple" is marked as a word about people, because "temple" is a noun after a group |
| The pairs that are read | Only a pair that is a phrase of the lexicon. "A Hindu temple" is one. "A Muslim church" is none, and is reported as unread |
| A school | A word for a group or for a building of worship, followed by "school" or "schools", is a community's amenity, as "Muslim schools" is today. "Church school" is read so, and "church" in it is no church |

### 5.5 `grammar.py`

| Change | Detail |
|---|---|
| `about_a_campus` | Becomes a rule of every feature that is weighed on request for a fairness reason: the campus and the nine. Under a word that turns a thing away, the wish is a wish about people |
| Words that turn | "not many", "fewer", "less", "no", "without", "away from", "far from", "not near", "nowhere near". Those that the grammar does not yet hold as a turn before a thing are added, so that sentences 25 to 28 are read and are not left unread |
| `no_measure` | Unchanged in shape. It no longer meets a place of worship, because none is a phrase of `NO_MEASURE` |

### 5.6 `interpret.py`

| Change | Detail |
|---|---|
| `_offered` | A feature that is weighed on request is offered with two choices, to add it and to ignore it. Where the spec holds it, to take it off and to leave it. Never `less` |
| A campus | Stays as it is: applied when it is asked for plainly, and never offered. The nine differ, by rule 1 of section 1 |
| The notice with an offer | Already possible: a notice stands today beside edits and beside offers |

### 5.7 `reducer.py` and `rank.py`

No change is expected. The reducer asks `direction_allowed` of every edit, and a feature whose polarity is `more` has one direction. The test of 5.8 holds it.

### 5.8 Tests in `packages/core/tests`

| Test | What it holds |
|---|---|
| `test_interpret.py`, `COMMUNITY_AMENITIES` | Loses "near a mosque" and "close to a church". Keeps the shops, the bars and the schools |
| `test_interpret.py`, new: `test_a_building_of_worship_is_offered_and_never_applied` | Sentences 1 to 16: the offer, its one feature, no edit, no notice |
| `test_interpret.py`, new: `test_a_word_for_a_belief_before_a_building_names_the_building` | Sentences 5 to 8: no notice |
| `test_interpret.py`, new: `test_a_wish_to_be_kept_from_a_building_of_worship_is_a_wish_about_people` | Sentences 25 to 28, and each with every word that turns: the notice, no offer, no edit |
| `test_interpret.py`, new: `test_a_sentence_about_people_offers_no_building` | Sentences 20 to 24: no row of `suggestions` names a feature of worship |
| `test_interpret.py`, new: `test_an_offer_of_worship_has_no_choice_of_less` | For each of the nine, in a spec with it and without: the choices |
| `test_interpret.py`, `test_the_policy_lexicon_holds_words_for_people_and_never_for_buildings` | Its list of buildings gains the nouns of `_WORSHIP` |
| `test_catalogue.py`, `RESIDENT_WORDS` | Gains words for those who go to a building: worshippers, congregation, believers, and the plural nouns for the followers of a belief. No label, unit, definition or note may hold one |
| `test_catalogue.py`, new: `test_a_place_of_worship_is_weighed_on_request_and_is_in_no_vibe_and_no_likeness` | The kind, `in_likeness`, and every recipe |
| `test_reducer.py` or `test_rank.py`, new: `test_a_weight_on_a_place_of_worship_cannot_be_turned_toward_fewer` | An edit with the direction `less` is rejected for each of the nine |
| `test_vocabulary.py` | The words of `_WORSHIP` are words of the vocabulary |

## 6. What must change outside core

| Where | Change |
|---|---|
| `contracts/openapi.json` | Made again with `make openapi`: nine values of `FeatureId`. `docs/design/contract.md`, section 8.4: the row "For a community's amenities" loses the mosque, and a row is added for a building of worship |
| `services/api/src/burro_api/reader.py` | The words given to a model say today that a place of worship is reported as unmet. They must say instead that a place of worship named as a building is proposed as its feature, never with a direction of less, and that a wish to be kept from one is `avoid_group` |
| `apps/web/src/content/search.ts` | The words for `community_amenities` say today that Burro has no data on places of worship. Proposed: "Burro has no data on shops, places to eat, venues or schools of one community, so that part was left out." |
| `apps/web`, the offer | A row of `suggestions` is shown as any offer is. Its note is shown with it, in full, before the person chooses |
| `apps/web`, an area's page | Section 8, question 3 |
| `apps/web` and `apps/ios`, generated types | Made again from the contract |
| A share | A share stores a spec. A spec that weighs a mosque says something of the person who made it. Section 8, question 4 |
| `evals/reader/cases/who_lives_there.jsonl` | Cases `who-013`, `who-035` and `who-036` expect `community_amenities` for a mosque, a synagogue and a church. A case says what a careful person would do, so each is put right to expect the offer, with the founder's decision as the reason. New cases are added at the end for sentences 5 to 8 and 25 to 28. No id is reused |
| `packages/pipeline/src/burro_pipeline/release/synthetic/` | The made-up city gains a figure for each of the nine, drawn from a stream of its own, so that no figure that was there moves. `make fixture` |
| `.claude/skills/verify/SKILL.md` | It says that "Near a mosque" is `ok` with `community_amenities` unmet. It must say that it is offered |
| `docs/adr/0006-rank-places-not-residents.md` | It says that a request for community is met through amenities. It must say which: the nine, each with one direction and on request. It is amended with the founder's decision, by whoever applies the decisions |

## 7. What is never built, and what holds it

| Never | Held by |
|---|---|
| A figure of who lives anywhere from a count of buildings | `test_a_count_of_buildings_is_never_turned_into_an_estimate_of_who_lives_there`, in the pipeline. No figure is a share or a rate. No file about who lives anywhere is opened |
| A count of buildings for each so many homes, or how many kinds are within reach | `test_what_is_handed_back_cannot_be_made_into_a_rate_or_a_count_of_kinds`, in the pipeline. What a measure hands back holds no count of homes. Whoever adds the nine to the measures of a build must not hand on the reach of cultural venues, which holds both |
| A score of how much of a community an area has | `test_the_counts_are_never_added_up_into_a_score_of_how_much_of_anything_an_area_has`. No kind is weighed against another. No figure says how many kinds are within reach. Core's `checked_recipe` keeps each out of every vibe |
| A direction of fewer | `test_a_count_is_never_offered_with_a_direction_of_fewer`, and the tests of 5.8 |
| A filter that takes areas in or leaves them out by a count of buildings | An area is taken in or left out by its id alone: a rule of an area names no feature. A test of 5.8 should hold that it cannot name one of the nine |
| Likeness by places of worship | `in_likeness` is false |
| A map coloured by a count of one kind | The features are in no vibe, and a lens is a vibe's |
| A word about people turned into a building | Rule 4 of section 1, and `test_a_sentence_about_people_offers_no_building` |

## 8. Questions for the founder

| # | Question | What each answer gives |
|---|---|---|
| 1 | Is a place of worship offered, or applied when it is asked for plainly? | Offered, as proposed: the person sees what is counted before they choose. Applied, as a campus is: one step fewer, and the note is seen only afterwards |
| 2 | Is an area put in order by how many buildings of a kind are within reach, or by whether one is? | How many: what is built. It sets an area with five above an area with one. A person may read that order as a sign of who lives where, though no figure says so. It also rises where one building has several records that stand apart. Whether one is: it answers "near a mosque" as it was asked, it is open to neither, and it is the same however many records a building has. It is one more figure for each kind, by the same code |
| 3 | On an area's page, are the counts shown to everyone, or only the kinds a person asked for? | To everyone: a newcomer sees what is there. It puts a count of the buildings of each belief on every page. Only when asked: nothing is shown that was not sought |
| 4 | Does a share keep the kind of place of worship a person weighed? | Kept: the link gives the same ranking. Made coarser, to a place of worship of no kind named: the link says less of the person who made it, and gives another ranking |
| 5 | May the places to eat that the file files as halal or as kosher be counted, on request and with one direction? | It would answer "kosher restaurants nearby". It is a count of one kind of food as a way to a community, which is what the decision names as a food shop. The file's categories of shops could not be read, so nothing is known of a kosher or a halal shop |
| 6 | Is a shrine, a monastery, a convent, an ashram or a Zen centre a place of worship? | The publisher files each apart. Counted, a Zen centre and an ashram add to the temples. Left out, as built, the count is of what the publisher calls a place of worship |
| 7 | Are churches told apart by denomination where the file says? | It would answer "a Catholic church". How many records say their denomination is not known until the file is read |
