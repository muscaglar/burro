# 0007. Close legal questions by design

Status: accepted, 2026-09-23. Amended the same day: Burro relies on published licences, and no launch waits on a reply from a data owner.

## Context

The first plan assumed a solicitor would review four things before launch, at an estimated GBP 5,000 to 10,000. The founder rejected that cost. So nothing in v1 may depend on a legal opinion.

## Decision

For each open question, take the most conservative design that still delivers the product, and write down what is left over.

| Question | How it is closed | What is left over |
|---|---|---|
| Could ranking areas amount to steering? | Rank places, never residents. See 0006 | Proxy effects, covered by the audit |
| Does share-alike reach the travel-time table? | Follow the published guidelines, publish the method, credit OSM. See 0004 | Being asked to publish the table. Accepted |
| May Price Paid be aggregated by postcode? | Rely on the published terms, which allow showing price information. Never display postcode rows | Low. Standard practice |
| Privacy notice, DPIA, terms | Written from the regulator's templates. Vendor agreements accepted online | Unreviewed wording |
| Rail and GLA licence terms | Read, save and register them. Where an owner publishes no licence at all, leave the source out until a person answers | A source may be left out |

### Published licences are relied on

- A source is used on the terms its owner publishes. Most are under the Open Government Licence, which allows commercial use. Each is credited as its licence asks.
- A question put to a data owner is a courtesy and a record. It is never a condition of launch, and nothing in the schedule waits on a reply.
- Where an owner publishes no licence, or reserves all rights, the source is left out until a person gives an answer to the question asked. That Burro is free at launch does not change this: with no licence, the default is that a work may not be reused.
- An automatic reply says that a message arrived. It is not an answer, and it is never recorded as a permission.
- A reply from a data owner is kept privately, because it holds a person's name and words. `registry/evidence/` holds a dated note of what was asked and answered, and nothing more.
- Burro is treated as commercial. It is free at launch, and a paid tier is planned.

## Consequences

- No professional has reviewed any of this. The plan says so plainly.
- Some features are more cautious than the law may require.
- A source with no published licence is left out, not argued over.

## What would change it

Revenue. The first thing to buy is a capped fixed-fee review of the privacy documents. Free legal clinics for startups are worth applying to before then.
