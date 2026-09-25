# Where to look

The way in to every guide. Find what you want to do, and open the one guide beside it. Every guide under `docs/` and `deploy/` is reached from this page in two steps at most, and [a test](../tools/tests/test_guides_are_found.py) holds the page to that.

## To run it

| You want to | Read |
|---|---|
| Know what Burro is, and what state each part is in | [The README](../README.md) |
| Run the API and the website on a machine of your own | [The README, "See the website"](../README.md#see-the-website) |
| Run the iPhone app | [apps/ios/README.md](../apps/ios/README.md) |
| Open the review desk and its panel | [The desk, in five minutes](desk-guide.md) |

## To deploy it

| You want to | Read |
|---|---|
| Put the website and the API on the internet | [Putting Burro on the internet](../deploy/README.md) |
| Set the project up at Vercel | [The website on Vercel](../deploy/web/README.md) |
| Serve a release of London, or go back to the one before | [The same guide, "Serving a release of London"](../deploy/README.md#serving-a-release-of-london) |
| Turn a model on, or change how many calls it may be sent | [The same guide, "Turning the model on"](../deploy/README.md#turning-the-model-on) |

## To refresh the data

| You want to | Read |
|---|---|
| Refresh London, from what is due to what is served | [Refreshing London](refreshing-london.md) |
| Make the buckets, the keys and the environments, start a hosted run, and read what it prints | [Data builds](data-builds.md) |
| Build London in a hosted run, and approve the release | [Data builds, "London, from the bucket to the service"](data-builds.md#london-from-the-bucket-to-the-service) |
| Change a name, a recipe or the table of brands | [The desk, in five minutes](desk-guide.md) |
| Add a data source, or check a licence | [registry/README.md](../registry/README.md) |

## To add a city

| You want to | Read |
|---|---|
| Know what a second city would take, and in what order | [Adding a city](adding-a-city.md) |

## To change the code

| You want to | Read |
|---|---|
| Know the commands, the rules and where things live | [AGENTS.md](../AGENTS.md) |
| See how the parts fit, and what holds each promise | [The whole of Burro, in four pictures](architecture.md) |
| Look up a record, a rule or a route | [The contract](design/contract.md) |
| Change the engine, the pipeline or the API | [packages/core](../packages/core/AGENTS.md), [packages/pipeline](../packages/pipeline/AGENTS.md), [services/api](../services/api/AGENTS.md) |
| Change the website or the iPhone app | [apps/web](../apps/web/AGENTS.md), [apps/ios](../apps/ios/AGENTS.md) |
| Change the review desk, or the cases the reader is scored on | [tools/desk](../tools/desk/AGENTS.md), [evals](../evals/AGENTS.md) |
| Drive a change before you say it works | [Verifying a change in Burro](../.claude/skills/verify/SKILL.md) |

## To know why a thing is as it is

| You want to | Read |
|---|---|
| Know what was decided, and why | [The decision records](adr/README.md), listed below |
| Know how Burro got here, and what went wrong on the way | [How Burro got here](history.md) |
| Know what is planned, and what is left | [The plan](PLAN.md) |
| See the evidence the plan rests on | [The research](research/README.md), which lists every page of it |
| Read the privacy notice and the terms, as drafts | [The legal drafts](legal/README.md) |

## The designs, under `design/`

**The truth of today.** Each says what is built. Where one and the code disagree, one of the two is wrong, and is changed.

| Design | What it holds |
|---|---|
| [contract.md](design/contract.md) | How core, the release and the API fit: every record, rule and route. `make ci` holds the code to it |
| [web.md](design/web.md) | The website: every page, state and control |
| [models.md](design/models.md) | Four providers of a model behind one interface, and what must hold before one reads |
| [desk.md](design/desk.md) | The review desk and its queues |
| [panel.md](design/panel.md) | The panel: how a change a person keeps reaches a build |
| [london-data.md](design/london-data.md) | The plan for real data for all of London, by milestone. It stands where one of the designs behind it disagrees |
| [what-core-needs.md](design/what-core-needs.md) | What core still waits on, measure by measure |

**Not built.** Each is a design of what is still to come, and describes no code.

| Design | What it holds |
|---|---|
| [london-data-travel.md](design/london-data-travel.md) | Travel times: the engine, the sizes and the method. Built for a made-up town alone |
| [london-data-timetables.md](design/london-data-timetables.md) | What a journey time needs of each publisher, and what must be signed for it |
| [london-data-researcher.md](design/london-data-researcher.md) | A model that helps when a release is built, and never answers from memory |
| [community-reader.md](design/community-reader.md) | How a place of worship or a centre would be offered from what a person types |
| [premium.md](design/premium.md) | The paid tier: the choices, and what to keep open |

**History, kept for the reasoning.** Each was built from, or overtaken. Where one differs from the contract or the code, it is the one that is out of date.

| Design | What it holds |
|---|---|
| [vibes.md](design/vibes.md) | The design the vibes were built from |
| [vibes-proposal-newcomer.md](design/vibes-proposal-newcomer.md) | The first of the three proposals it was merged from: vibes, designed from the person |
| [vibes-proposal-evidence.md](design/vibes-proposal-evidence.md) | The second: vibes, designed from the data |
| [vibes-proposal-difference.md](design/vibes-proposal-difference.md) | The third: what Burro can do that a portal cannot |
| [slice-1.md](design/slice-1.md) | The first slice of the vibes: what was specified, what was built and what was found |
| [residents-age-and-households.md](design/residents-age-and-households.md) | What was proposed, and then built, of the age of residents and of their households |
| [heritage-measures.md](design/heritage-measures.md) | What conservation areas and listed buildings asked of core and of the website |
| [london-data-areas.md](design/london-data-areas.md) | Named areas for all of London, and what each draft did where the design was open |
| [london-data-census.md](design/london-data-census.md) | Census figures on the page of an area, as designed before they were built |
| [london-data-pipeline.md](design/london-data-pipeline.md) | The pipeline and the store of evidence, as designed before the first fetch |
| [london-data-sources.md](design/london-data-sources.md) | The plan of ingest, source by source, as designed before the first fetch |

## The decisions, under `adr/`

[The list](adr/README.md) gives the state of each, in the order they were made. Here they are by what they are about.

| About | Record | What it decides |
|---|---|---|
| How the work is done | [0001](adr/0001-record-decisions.md) | Decisions are recorded, each with its reason |
|  | [0007](adr/0007-no-solicitor.md) | Legal questions are closed by design, with no solicitor |
|  | [0008](adr/0008-package-sources.md) | Where packages come from, and why no lockfile is committed yet |
|  | [0009](adr/0009-registry-in-toml.md) | The registry is TOML, one file for each topic |
|  | [0020](adr/0020-the-tests-run-side-by-side.md) | The tests run side by side, and what that asks of a test |
| The engine and the contract | [0002](adr/0002-deterministic-core.md) | A deterministic core, with a model at the edges |
|  | [0003](adr/0003-three-grids.md) | Three grids, and one table of cells |
|  | [0010](adr/0010-one-contract-one-synthetic-release.md) | One contract, and a made-up release to build on |
|  | [0024](adr/0024-an-area-with-no-figure-for-what-was-asked-stands-below.md) | An area with no figure for what was asked stands below every area that has one |
| What people type, and the model | [0005](adr/0005-raw-prompts-are-never-stored.md) | Raw prompts are never stored |
|  | [0011](adr/0011-nothing-is-kept-for-a-search.md) | Nothing is kept for a search |
|  | [0012](adr/0012-a-closed-vocabulary-and-a-guard-on-the-model.md) | The reader applies a plain prompt and asks about any other, and a model proposes |
|  | [0019](adr/0019-no-one-provider-and-a-key-alone-turns-nothing-on.md) | No one provider of a model, and a key alone turns nothing on |
|  | [0023](adr/0023-what-is-typed-goes-as-typed-and-people-are-told.md) | What is typed goes to the provider as typed, and people are told so |
|  | [0032](adr/0032-calls-to-a-model-are-capped-for-the-whole-service.md) | Calls to a model are capped for the whole service, and nobody is told apart |
| Who lives in a place | [0006](adr/0006-rank-places-not-residents.md) | Rank places, never residents |
|  | [0014](adr/0014-evidence-first-and-census-figures-shown.md) | Evidence first, and census figures are shown |
|  | [0028](adr/0028-household-income-is-shown-and-never-ranked-on.md) | Household income is shown, and never ranked on |
| Licences and sources | [0004](adr/0004-openstreetmap.md) | OpenStreetMap is for the basemap and for routing only |
|  | [0016](adr/0016-geography-behind-a-measure.md) | The geography behind a measure is registered for scoring |
|  | [0022](adr/0022-one-official-publisher-is-enough-for-a-name.md) | One official publisher is enough for a name |
| Builds and releases | [0015](adr/0015-where-builds-run-and-what-gates-a-launch.md) | Builds run in hosted CI from a private store, and what gates a launch |
|  | [0017](adr/0017-a-preview-says-it-is-one.md) | A preview says that it is one |
|  | [0018](adr/0018-a-real-release-is-served-with-its-evidence.md) | A release that is not made up is served only with its evidence |
|  | [0029](adr/0029-a-change-reaches-a-release-through-a-file-of-changes.md) | A change at the panel reaches a release through a file of changes |
|  | [0030](adr/0030-a-release-is-kept-approved-by-its-lock-and-carried-in-the-image.md) | A release is kept in a bucket of its own, approved by its lock, and carried in the image |
| Vibes and measures | [0013](adr/0013-vibes-are-the-centre.md) | Vibes are the centre, and how Gritty and Village feel are served |
|  | [0021](adr/0021-a-price-is-shown-as-the-publisher-gives-it.md) | What a home sells or lets for is shown as its publisher gives it |
|  | [0025](adr/0025-an-area-bears-a-drafted-name-and-says-so.md) | An area bears a drafted name, and says that it is a draft |
|  | [0026](adr/0026-the-chains-in-a-place-are-measured-by-a-table-of-tiers.md) | The chains in a place are measured by a table of tiers |
|  | [0027](adr/0027-a-journey-is-estimated-from-distance-until-a-timetable-is-held.md) | A journey is estimated from distance until a timetable is held |
|  | [0031](adr/0031-the-traffic-near-homes-is-a-measure.md) | The traffic near homes is a measure, and an area with no figure is never taken to have little |
