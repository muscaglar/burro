# 0006. Rank places, never residents

Status: accepted, 2026-09-23. Not reviewed by a lawyer. Amended the same day by [0014](0014-evidence-first-and-census-figures-shown.md): census figures about residents are now shown on an area's page. They are still never ranked on.

## Context

A product that recommends where to live can steer people toward or away from areas according to who lives there. The Equality Act 2010 bars service providers from discriminating, and treats segregation by race as less favourable treatment. US property portals withdrew even crime data over this concern.

The original brief listed demographics as an input to "vibe". There is no budget for a legal opinion on where the line sits, so Burro takes the position that needs none.

## Decision

- Nothing that describes who lives somewhere feeds ranking or any tag. That includes age, household composition and student share.
- Housing facts are allowed because they describe buildings: dwelling type, build period, density. Tenure describes households, so it is shown on profiles and not ranked on, until the founder decides otherwise.
- Tags are named for the place. "Family amenities" is built from schools, nurseries and play space. "Near universities" is built from distance to campuses.
- Ethnicity, religion, country of birth, language, sexual orientation, gender identity, disability, health and age tables never feed a score, a tag or a vibe. The registry refuses any entry that gives them a use in scoring, and the gate refuses a registry that breaks a rule. Since [0014](0014-evidence-first-and-census-figures-shown.md) the census tables for age, household type, country of birth, ethnic group, religion and main language may be shown on an area's page, as a table of the statistics office's own figures and nothing more. The rest stay for the audit alone.
- Some files mix the two. The deprivation indicators hold noise exposure beside income and health; the population estimates hold totals beside age and sex. The gate works per source, so these are fenced by the conditions on the registry entry and by the feature allowlist, which names the columns that may be used.
- The model can only emit feature IDs from an allowlist in code.
- A request to avoid a group gets one neutral sentence, and the rest of the query is served. A request for community is met through amenities: places of worship, specialist shops, venues.
- A wish to be far from a campus is a request to avoid a group said another way, and gets the same sentence. The feature for universities has one direction: a person may ask to be near one. Decided, 2026-09-23.
- A word for a group is never left to be read as a feature or a tag. "Gay village" is a request about people and not a wish for a village; "muslim schools" is a request for a community's amenity and not a weight on school results.
- Recorded crime is off by default, shown as rates by category with caveats, and never labelled safe or unsafe.
- The same structured preferences give the same results for every user.

### The proxy audit

A neutral feature can still correlate with a protected group. Before the audit runs, each feature has written down: the aim it serves, why it is proportionate, the correlation that triggers a review, and what can be done (drop it, cap its weight, make it opt-in). Finding a correlation and doing nothing is worse than not looking.

## Consequences

- "Lots of young families" cannot be asked for directly. "Good primary schools and playgrounds" can.
- Some vibe signal is lost. What remains is defensible.

## What would change it

Legal advice that a specific resident-based input is safe, paid for once the product earns money.
