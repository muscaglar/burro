# 0006. Rank places, never residents

Status: accepted, 2026-09-23. Not reviewed by a lawyer. Amended the same day by [0014](0014-evidence-first-and-census-figures-shown.md): census figures about residents are now shown on an area's page. They are still never ranked on. **Amended on 2026-09-24** by the founder's decision: the age of residents and what their households are made of may feed a vibe and a ranking, and one vibe may count recorded crime where a person asks for it by name. See "Amended, 2026-09-24", below, which says what in this record it changes. Amended on 2026-09-24 by [0013](0013-vibes-are-the-centre.md): recorded criminal damage and recorded anti-social behaviour are parts of one vibe, Gritty, in a release of London as in a made-up one, and are 45 in 100 of its recipe. They say what was recorded in a place, and nothing of who lives there. To type "gritty" is to ask for recorded crime by name. Nothing else of this record is changed by it: recorded crime is off by default and counts only when a person asks for it by name, and "safe" is still no such request. Amended on 2026-09-24: one name of a measure may say residents. See "One name may say residents", below. **Amended on 2026-09-25** by the founder's decision: the proxy audit is dropped. No measure waits on a row of it, and none is held back for want of one. See "Amended, 2026-09-25", below, which says what was decided before and what is decided now.

## Context

A product that recommends where to live can steer people toward or away from areas according to who lives there. The Equality Act 2010 bars service providers from discriminating, and treats segregation by race as less favourable treatment. US property portals withdrew even crime data over this concern.

The original brief listed demographics as an input to "vibe". There is no budget for a legal opinion on where the line sits, so Burro takes the position that needs none.

## Decision

- Nothing that describes who lives somewhere feeds ranking or any tag. That includes age, household composition and student share. **Changed on 2026-09-24** for age and household composition, and for nothing else.
- Housing facts are allowed because they describe buildings: dwelling type, build period, density. Tenure describes households, so it is shown on profiles and not ranked on, until the founder decides otherwise.
- Tags are named for the place. "Family amenities" is built from schools, nurseries and play space. "Near universities" is built from distance to campuses.
- Ethnicity, religion, country of birth, language, sexual orientation, gender identity, disability, health and age tables never feed a score, a tag or a vibe. The registry refuses any entry that gives them a use in scoring, and the gate refuses a registry that breaks a rule. Since [0014](0014-evidence-first-and-census-figures-shown.md) the census tables for age, household type, country of birth, ethnic group, religion and main language may be shown on an area's page, as a table of the statistics office's own figures and nothing more. The rest stay for the audit alone. **Since 2026-09-25** no audit is planned, and the rest are read for nothing.
- Some files mix the two. The deprivation indicators hold noise exposure beside income and health; the population estimates hold totals beside age and sex. The gate works per source, so these are fenced by the conditions on the registry entry and by the feature allowlist, which names the columns that may be used.
- The model can only emit feature IDs from an allowlist in code.
- A request to avoid a group gets one neutral sentence, and the rest of the query is served. A request for community is met through amenities: places of worship, specialist shops, venues.
- A wish to be far from a campus is a request to avoid a group said another way, and gets the same sentence. The feature for universities has one direction: a person may ask to be near one. Decided, 2026-09-23.
- A word for a group is never left to be read as a feature or a tag. "Gay village" is a request about people and not a wish for a village; "muslim schools" is a request for a community's amenity and not a weight on school results.
- Recorded crime is off by default, shown as rates by category with caveats, and never labelled safe or unsafe. It counts only when a person asks for it by name, in a measure or in the one vibe that holds it, which is Gritty. A word that is only read into Gritty, "edgy", "affluent", is offered and never applied, and every choice that would weigh Gritty says on its face that it counts recorded crime. "Safe" is never applied: Burro cannot say how safe a place is, and says so.
- The same structured preferences give the same results for every user.

### One name may say residents

Amended, 2026-09-24. No word for who lives somewhere stands in the name of anything a person can rank on, and a test holds every name of the catalogue to a list of such words. One name is let through: "Share of residents exposed to 55 dB or more of transport noise".

- Its file counts who is exposed and gives no count of homes. A name that left the word out said nothing of whose share it was, and a name that said homes was untrue.
- The measure is of a place: how loud it is where people live. The residents are how the places of a small area are weighed. It says nothing of who they are: no age, no income, no health, no origin.
- The guard lets the name through as the whole of a name, as it is written. A word more or a word less is refused as any other name is, and so is any other name that says residents. `test_the_guard_lets_the_one_name_of_transport_noise_through_and_refuses_every_other` holds it to that.
- Its short label, "Less transport noise", and the words that compare two areas say nothing of who.

### The proxy audit

**Dropped on 2026-09-25.** What follows is what was decided before. It is kept as the record of it, and asks nothing of a measure now. See "Amended, 2026-09-25", below.

A neutral feature can still correlate with a protected group. Before the audit runs, each feature has written down: the aim it serves, why it is proportionate, the correlation that triggers a review, and what can be done (drop it, cap its weight, make it opt-in). Finding a correlation and doing nothing is worse than not looking.

The first row is written: [recorded criminal damage and anti-social behaviour](../research/data/incidents.md), section 11. It says what the two measures were held against, and that nothing about residents could be. The second is written: [the age of residents and what their households are made of](../design/residents-age-and-households.md), section 12, for the four measures and the two vibes that hold one. It says what each was held against, and that nothing of what was not decided on could be. No audit has run.

A second row is written: [what homes sell for, the council tax bands and the rise in prices](../research/data/prices.md), section 7. It is the first that was held against a figure of residents: the statistics office's estimate of household income, which the registry allows a check to read. Two of its measures stand at or over the line the row sets. [0028](0028-household-income-is-shown-and-never-ranked-on.md) says what was found and what is the founder's to decide.

## Amended, 2026-09-24

The founder was told that the registry refused every figure about residents, and decided that it should not: the age of the people who live in an area and what their households are made of are part of what a place is like. Asked about each kind of figure in turn, the founder decided as below. No lawyer was asked, and [0007](0007-no-solicitor.md) still holds.

### What changed

| Matter | Until now | Decided |
|---|---|---|
| The age of residents, and what households are made of | Never fed a score, a tag or a vibe | May feed a vibe and a ranking, from the census tables of age and of household composition and from nothing else |
| Which way such a figure may be asked for | | For more of what it counts, and never for fewer. It is no end of a scale and no filter |
| Recorded crime | Kept out of every tag and every vibe of a real release | One vibe, Gritty, counts recorded criminal damage and recorded anti-social behaviour among its parts. To ask for Gritty by name, towards either end, is to ask for recorded crime by name. [0013](0013-vibes-are-the-centre.md) holds the recipe |

### What was asked, and did not change

| Matter | Decided |
|---|---|
| Ethnic group and religion | Shown on an area's page and never ranked on, as [0014](0014-evidence-first-and-census-figures-shown.md) has it. A wish for a community is met only through what is there: places of worship, cultural centres, food shops |
| Ranking towards a community a person names, and never away from one | Weighed, and kept open. It is not built, and it is not to be built without a new decision |
| A filter that includes or excludes an area by who lives there | Not built. Nobody asked for one |
| A wish for fewer of any group of people | Nothing reads one. The person is told so in one sentence, and the rest of what they asked is answered. This holds for age and for households too |
| Stop and search | Never read, whatever this record says of residents. It records whom the police stopped, and not who lives in a place |
| The police file as saved | The crime files alone are read. The outcomes and the stop and search files are never opened |
| Gender | Left out. Every area is close to even |
| The religious character of a school | It is no amenity. Schools are counted without regard to faith, and the column is never read |

### What was not asked, and stands

Country of birth is shown and never ranked on. Income, employment, health, qualifications, language, disability, sexual orientation and gender identity never feed a score, a tag or a vibe. Recorded crime is never labelled safe or unsafe, and outside Gritty it counts only when a person asks for it or switches it on. The model can only emit feature ids from a list in code. The same settings give the same results to everyone. A word for a group is never read as a feature.

### Rule 8, reworded

| | Rule 8 of AGENTS.md |
|---|---|
| Before | Rank places, never residents. Nothing that describes who lives somewhere may feed ranking or a tag. Protected-characteristic data is registered as `audit_only`, which the gate keeps out of scoring, or under `residents` for the one use `census_table`, which the gate lets into the census table on an area's page and nothing else. |
| After | Rank places. Of residents, only their age and the make-up of their households may feed ranking, a tag or a vibe, from the census, and only towards more of what a figure counts. Nothing else that describes who lives somewhere may, and nothing reads a wish for fewer of any group of people. Ethnic group, religion and country of birth are shown on an area's page and never ranked on. Stop and search data is never read. Protected-characteristic data is registered as `audit_only`, which the gate keeps out of scoring, or under `residents`, which the gate lets into the census table on an area's page, and into scoring for the tables of age and of household composition alone. |

### Why the line is drawn where it is

[The reading of the law](../legal/residents-crime-and-equality.md) was made from the Equality Act as printed and from the ICO's pages. It is not advice. In short:

| Figure | Where it stands | Why |
|---|---|---|
| Age, and what households are made of | Ranked on, on request | They say what stage of life an area is lived at. The Act lets direct discrimination by age be justified, and its part on letting and selling does not apply to age |
| Ethnic group and religion | Shown, never ranked on | The Act treats race most strictly: to segregate by race is less favourable treatment in itself. A control that sorted areas by race or religion would be a tool for steering |
| Stop and search | Never read | Each row is about one person. It says nothing of who lives in a place |

### How it is held

- The licence registry holds the two census tables under `residents`, in an entry of their own that is approved for scoring. Its rule lets a source under `residents` list scoring only where every table it names is one of the two. Every other census table about residents is held as it was.
- A figure about who lives somewhere says so in its name, and says beside it on the page what is counted, of whom, and that it was counted on 21 March 2021, during a lockdown. The statistics office says the pandemic may have affected where some people were counted, and names students and some urban areas.
- A figure about residents is never read low in a recipe, never stands in a vibe with two ends, and never counts towards how alike two areas are.
- Household composition is no protected characteristic, but the table of it names marriage and civil partnership, which is. No figure is made from that part of the table.
- Core's list of features is closed. A feature that describes residents is one of a list that is written out, each with a name that says who is counted and in which census, and each asked for in one direction. What core must change is in [the design](../design/residents-age-and-households.md).
- Student share and tenure were not asked about. Each stands as it did.

### What is left over

- The title no longer says the whole of it. It is kept, because every other record names this one by it.
- Age is itself a protected characteristic, and what households are made of follows age, sex and marriage. So the proxy audit now has inputs that are about residents by design. Its written rule must exist before a measure of either is in a release. It is written: [the design](../design/residents-age-and-households.md), section 12. The audit itself has not run. **Dropped on 2026-09-25**: no audit is to run, and the row holds nothing back.
- A rate of recorded crime that a publisher has divided by a count of residents, or has smoothed by the kind of people who live in an area, brings residents into a measure that is said to be of the place. Whether such a rate may feed Gritty is for the founder to decide before a figure is shown.
- The age of residents and their households are built, since 2026-09-24. Core holds four measures, each a share in 100 with the census in its name, and two vibes that hold one each at 40 in 100: Family area and Young professionals. A phrase for any of them is offered and never applied, towards more and no other way, and a wish for fewer of anyone draws the notice and nothing else. No release may hold a count of people, and nothing else may describe residents: each is a test. [The design](../design/residents-age-and-households.md), section 13, says what was built and what was chosen. Gritty is built: [0013](0013-vibes-are-the-centre.md) says how.
- The equality regulator's own guidance for service providers has not been read.

## Amended, 2026-09-25

The founder was asked what to do about the proxy audit, and decided that it is dropped. It was the fourth of the questions put to them, and these are their words, as they wrote them:

> Lets ignore (4)/delete it. Race and relgiion is important in understanding an area.

No lawyer was asked, and [0007](0007-no-solicitor.md) still holds.

### What was decided before, and what is decided now

| Matter | Decided before | Decided on 2026-09-25 |
|---|---|---|
| The proxy audit | A check, run offline, that no measure stands in for a protected characteristic. A written rule was to come before it ran | Dropped. No audit is run, and none is planned. Its rule was never written, no store was made for it, and it never ran |
| A row of the audit, before a measure joins a release | Asked of a measure that might follow who lives somewhere: what it was held against, what triggers a review, and what can then be done | Not asked. No measure waits on a row, and none is held back for want of one |
| The rows that were written | Four, each by hand: [recorded incidents](../research/data/incidents.md), [the age of residents and their households](../design/residents-age-and-households.md), [the brands](../research/data/brands.md) and [prices](../research/data/prices.md) | Each stays where it is, as a record of what was measured. Each says that the audit was dropped, and holds nothing back |
| The lines at which a measure is reviewed, loses its place or is dropped | The design of the vibes proposed 0.3, 0.5 and 0.6, and each row gave 0.5 as what triggers a review. No line was adopted | Gone with the audit. No figure of a row triggers anything |
| Private outdoor space | Held out of every release until its row had passed, and for no other reason | Carried. A build that names its files works it out, and it is 25 in 100 of Houses or flats, as the recipe says |
| The census tables of protected characteristics, in the licence registry | Gated, under the heading `audit`, for the audit alone | Gated still, under the same heading, with no use. The entry says that no audit is planned |

### What stays, exactly as it was

Nothing that keeps residents out of a ranking is loosened. Each line below is held by the tests that held it before, and none of them was changed.

| What stays | Held by |
|---|---|
| The gate keeps data of protected characteristics out of scoring. Ethnic group, religion and country of birth are shown on an area's page and are ranked on nowhere: not in a search, a comparison, a share, a likeness or an explanation | `test_contained_sources_are_refused_for_every_use`, `test_no_real_table_of_ethnic_group_religion_or_country_of_birth_may_be_scored` and `test_the_real_audit_entry_has_no_use_that_reaches_a_page` in the pipeline's `test_registry_gate.py`. `test_no_search_can_ask_for_a_census_figure`, `test_no_comparison_can_ask_for_a_census_figure`, `test_no_share_and_no_explanation_can_ask_for_a_census_figure` and `test_moving_the_census_between_areas_changes_no_answer_of_sixty_searches` in the API's `test_census.py`. `test_likeness_is_never_counted_on_who_lives_somewhere_whatever_a_flag_says` in core |
| No reading of any words asks for fewer of any group of people | `test_request_to_avoid_a_group_gets_the_neutral_notice_and_the_rest_is_served`, `test_a_word_that_turns_before_who_is_counted_draws_the_notice_and_nothing_else` and `test_no_choice_of_what_counts_who_lives_somewhere_is_ever_less` in core's `test_interpret.py` |
| A part that counts residents is read high and never low, stands in a one-way vibe and never in a scale, counts towards no likeness, is never applied from a word, and is never taken by one press | `test_a_recipe_that_counts_residents_is_read_high_runs_one_way_and_is_no_one_figure` in core's `test_catalogue.py`, `test_a_spec_may_ask_for_more_of_who_is_counted_and_never_for_fewer` in `test_spec.py`, `test_a_phrase_for_who_is_counted_is_offered_towards_more_and_never_applied` in `test_interpret.py`, and `test_the_words_the_rules_offer_who_is_counted_for_are_the_rules_to_read` in the API's `test_adversary.py` |
| Household income is shown and never ranked on ([0028](0028-household-income-is-shown-and-never-ranked-on.md)) | `test_no_search_no_comparison_and_no_explanation_can_ask_for_it` and `test_moving_the_income_between_areas_changes_no_answer_of_sixty_searches` in the API's `test_income.py`, and the pipeline's `test_the_list_of_household_income.py` |
| Stop and search is never read. The religious character of a school is never read | `test_a_reader_of_the_whole_zip_opens_the_crime_files_and_no_other` in the pipeline's `test_street_crime_files.py`, and `test_the_names_of_head_teachers_the_counts_of_pupils_and_religion_are_all_forbidden` in `test_schools_file.py` |

### What was not asked, and stands

Three things were said to wait on an audit, and the founder was asked about none of them. Each stands as it is built, and is the founder's to decide.

- Core counts no likeness on some measures of the place, each of which was held out until an audit had passed it: flats, homes per hectare and private outdoor space among them. They stay out of likeness. `_HELD_OUT_OF_LIKENESS` in core's catalogue is the list.
- A build shows main roads and ranks no area on them alone, because no audit of the figure had been run. It stays so. Quiet streets and Gritty still rest on the figure.
- On a release that is not made up every vibe holds the flags that core's one catalogue gives it. The design of the vibes had each flag start off, to be turned on by what the audit found. Nothing turns one off ([the contract](../design/contract.md), section 13).

### Rule 8, reworded

What it says of protected-characteristic data changed, and nothing else of it. It has as many words as it had. The registry still holds the use `audit_only`, which the gate gives to nothing a release is made of.

| | What rule 8 of AGENTS.md says of protected-characteristic data |
|---|---|
| Before | Protected-characteristic data is registered as `audit_only`, which the gate keeps out of scoring, or under `residents`, which the gate lets into the census table on an area's page, and into scoring for the tables of age and of household composition alone. |
| After | Protected-characteristic data sits under `audit`, which the gate keeps out of scoring and no audit reads, or `residents`, which it lets into the census table on an area's page, and into scoring for the tables of age and household composition alone. |

## Consequences

- "Lots of young families" cannot be asked for directly. "Good primary schools and playgrounds" can. **Since 2026-09-24** the first can be asked for too: it is offered as Family area, which a person adds by pressing it. "Fewer families" cannot, and never will be.
- Some vibe signal is lost. What remains is defensible.

## What would change it

Legal advice that a specific resident-based input is safe, paid for once the product earns money. The amendment of 2026-09-24 was made without it: the founder weighed the question and decided. Advice that ranking on age or on households is not safe would change it back. So would a complaint, or evidence that anyone uses Burro to steer people.
