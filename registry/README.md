# Licence registry

`sources/` lists every dataset Burro may touch, one file per topic: `housing.toml` holds housing sources and nothing else. Burro is a commercial product, so it must be able to prove it has the right to use each one.

The registry is enforced, not advisory. Pipeline code calls `Registry.require(id, use)` before it downloads anything. That call fails unless the source is approved for that use, or is gated or held and lists that internal use. Loading fails altogether if any entry breaks a rule, so the gate never answers from a bad registry.

```
make registry-check                 fails on any broken rule
make registry-check ARGS=--strict   warnings fail too; run before launch
uv run burro-registry list
uv run burro-registry attributions
```

## Status

| Status | Meaning | What the gate allows |
|---|---|---|
| `approved` | Licence confirmed from the publisher's own page. Commercial use allowed | The uses it lists |
| `gated` | Wanted for v1, but a named check must pass first | Only the internal uses it lists |
| `held` | Not used in v1 | Only the internal uses it lists |
| `banned` | Must never be used | Nothing |

Internal uses are `prototyping_only`, `validation_only` and `audit_only`. They exist so a spike can open a file and look at it before anyone relies on it. Nothing read this way may reach a data release.

`check` holds a release to that. The gate is asked again, of every file a figure rests on, for the use the figure is put to: `scoring` for a feature, a tag or a cost, `routing` for a journey, `display` for a station, `gazetteer` for a name or a boundary (ADR 0016). A figure that rests on a file fetched for an internal use, or on a file of a source that is not allowed for that use, is named under `input_is_allowed`, and the release is not fit to serve. A source that a file of the release cites, and that no figure put to the same use rests on a file of, is asked about for the use of that file, and the file is named under the same rule: the source of a place to reach is one. The registry is asked as it stands on the day of the check. A file that was read to validate against may be in the lock of a build, with no figure resting on it.

## Fields

| Field | Required | Notes |
|---|---|---|
| `id` | yes | Lowercase kebab-case, starts with the publisher: `hmlr-price-paid` |
| `name`, `publisher`, `url` | yes | `url` is the dataset's own page |
| `dimension` | yes | What the data is about |
| `tables` | under `residents` | Census table codes, as the statistics office writes them: `TS021`. A source under another heading may list its housing tables |
| `licence` | yes | One of the values in `model.py`. Use `Bespoke-terms` for a publisher's own terms |
| `additional_licences` | no | For datasets licensed per record |
| `licence_url` | no | The licence text |
| `commercial_use` | yes | `yes`, `yes_with_conditions`, `no`, `unknown` |
| `share_alike` | yes | True for ODbL and CC BY-SA |
| `attribution` | if approved | The publisher's exact required wording |
| `attribution_verified` | no | True only when the wording was read from the page itself, in a browser or as raw text, and the publisher states it for this dataset. A summary of the page does not count |
| `attribution_beside_figures` | no | True where the publisher asks that its statement stands wherever a figure made from the data is shown, and not on the page of attributions alone. A release says so of the source, and every fact that cites it carries the statement |
| `conditions` | if conditional | Anything Burro must do or never do with this data |
| `status`, `status_reason` | yes | A reason is required unless `approved` |
| `before_launch` | no | For an approved source: what must be settled before the product is public. Ingest is allowed meanwhile |
| `uses` | if approved | What Burro uses it for. The gate checks this |
| `cadence` | no | How often the publisher updates it |
| `verified_how` | yes | `primary_source`, `secondary_source`, `unverified` |
| `verified_on` | yes | A TOML date: `2026-09-23` |
| `evidence_urls` | if approved | Where the licence was confirmed |
| `file_urls` | if a file of it is fetched | The addresses its files are fetched from. Each is a whole address, or a prefix that ends in `/` and at the dataset. A file is fetched from no other address: see "What fetch asks of a source" |
| `notes` | no | |

## Rules

| Rule | Why |
|---|---|
| Approved sources need primary-source evidence, a use, and attribution wording | "Approved" has to mean something |
| Share-alike data stays out of the gazetteer and scoring | So the duty to publish derived data cannot reach them |
| Audit data has internal uses only | Nothing the audit reads may reach a user. The census table on an area's page is read under `residents`, never under `audit` |
| A source under `residents` lists `census_table` and no other use, internal uses included. It names its tables, and each is one an area's page may show | Census figures about residents are shown as the statistics office's own table and used for nothing else: no score, no vibe, no text, no search (ADR 0014) |
| A source under `residents` may list `scoring` as well, where every table it names is of age or of household composition: `TS007A` or `TS003`. Every table it names is asked about, wherever it names it: under `tables`, in its id, in its name and in every address it holds. It gains that use and no other | The founder decided on 24 September 2026 that the age and household make-up of residents may feed a vibe and a ranking. Nothing else about residents may ([ADR 0006](../docs/adr/0006-rank-places-not-residents.md), as amended that day). A source that names one table of any other kind is held as before |
| Only a source under `residents` lists `census_table` | So the census table can hold nothing else |
| A census table named under any other heading but `audit` is a housing table: `TS044`, `TS050` or `TS054` | So a table about residents cannot be registered where it could be scored. Every other census table is taken to be about residents, whether or not anyone has thought about it |
| An id appears once | Otherwise one entry could shadow a ban |
| An address under `file_urls` is https and holds no login, no part of a page after `#` and no letter outside ASCII. It reads one way only: no `..`, no `//`, no `\`, no space, and no sign encoded to hide one. A prefix is not the whole of a host, and holds no parameter | So that an address names one file or one dataset, and cannot be written to leave it |
| No entry names, under `file_urls`, an address that another entry holds: as a file, as its own page, or as its evidence | A publisher serves many datasets from one host. A file that one entry bans, holds or keeps for the audit must not pass under another |
| Gated, held and banned sources say why | The next person needs to know what would change it |
| Held sources have internal uses only; banned sources have none | |
| Non-commercial data cannot be approved or gated | |
| Links are https and carry no credentials | |
| A source sits in the file named for its dimension, and every file is named for one | So each file stays small enough to read, and none is skipped |
| Warning: attribution wording not yet confirmed | Must be fixed before launch |
| Warning: something is listed under `before_launch` | Must be settled before launch |
| Warning: verification older than a year | Licences change |

## What a data release asks of a source

The gate stands in two places. An ingest step calls `Registry.require(id, use)` before it reads anything, and `write_release` calls it again for every source a release cites, before it writes anything. The use it asks for depends on the file that names the source, so give a source every use it will be put to:

| The release file that names the source | The use it must be registered for |
|---|---|
| `catalogue.json`, `cost.json` | `scoring` |
| `travel.json` | `routing` |
| `stations.json` | `display` |
| `places.json` | `destination_search` |
| `neighbourhoods.json` | `gazetteer` |

A row names every source its figure was worked out from, the geography included: the lookup, the centres of output areas, the boundaries an area was measured on. Each is asked for the use of the file that names it, so a geography source behind a measure is registered for `scoring` as well as `cells`. See [ADR 0016](../docs/adr/0016-geography-behind-a-measure.md).

A release that is not synthetic is refused when no registry is passed. The synthetic release cites only the reserved id `synthetic`, which is no dataset and is not in the registry.

No file of a release asks for `census_table`, and a source under `residents` can list none of the uses above but `scoring`, which it can list only where every table it names is of age or of household composition. So a release that cites any other source about residents is refused, whichever file names it. The census table is to be kept in a folder of its own, outside the release, by a step that asks the gate for `census_table`. That step is not built yet: see [the design](../docs/design/london-data-census.md).

## What fetch asks of a source

Fetch holds a file of a list to the entry of its source, before it asks a publisher for anything. A publisher serves many datasets from one host, so the host of a file is not enough: a file passes only under the entry that names its address.

| What the list says of a file | What the entry holds |
|---|---|
| `source_id` and `use` | The gate allows the source for the use: see "Status" |
| `page`, where a person finds the file | The same address, letter for letter, as `url` or under `evidence_urls` |
| `url`, the address of the file itself | An address under `file_urls` that names it. A whole address names the same address, letter for letter and parameter for parameter. A prefix names every address under it |
| Its item, what it is, its edition and its address | No code of a census table but a housing table's, unless the entry is under `residents` or `audit` |

So for a file of an entry to be fetched, the entry needs this and no more:

1. `status = "approved"` and the use under `uses`. A `gated` or `held` entry may be fetched for an internal use it lists.
2. The page the list gives, as `url` or under `evidence_urls`.
3. The address of the file under `file_urls`, read on the publisher's own page and never built from a pattern. Write it in one of two ways, as the publisher's own addresses allow:
   - A whole address, where the publisher keeps many datasets in one folder or gives each file an id of its own. Name each file.
   - A prefix that ends in `/`, where the publisher's addresses name the dataset in the path. End it at the dataset: everything under it is a file of this entry and of no other. Never end it at a folder that holds other datasets, and never widen one to make a fetch pass.
4. `make registry-check`, then `uv run python -m burro_pipeline plan --list NAME --words`.

Fetch refuses an address the entry does not name with `why=18`, and one on a host the entry names nowhere with `why=13`. A file saved by hand is held in the same way, by the address it was saved from. What arrived is held too. Where a publisher sends a request on, the address it ends at is held: on a host the entry names, it is an address the entry holds, and on any other host it is no address that another entry holds. If it is neither, the file is not kept. Nor is a file kept that arrived from an address that can be read more than one way, on any host: one with `..` or a doubled `/` in it, a login, or a sign encoded to hide one. An address is taken to be another entry's however a server may have read it, as it is written or decoded again.

On a host that only the list names, under `may_redirect_to`, the rule holds this and no more: a file is refused if it came from an address that some entry names. An entry that names no address for its files keeps nothing off such a host, and on 2026-09-24 that is 83 of the 128 entries. The list names the hosts a request may be sent on to, and the registry entry does not. So read a change to `may_redirect_to` as closely as a change to an entry. Lists m1 and m2-places name four such hosts, as a fetch saw them, and the list m10-health names one more.

How the entries behind the lists stand on 2026-09-24:

| Publisher | How it names a file | What the entry names |
|---|---|---|
| Office for National Statistics, geography | `open-geography-portalx-ons.hub.arcgis.com/api/download/v1/items/ITEM/FORMAT`. The item is the dataset | A prefix that ends at the item |
| GOV.UK | `assets.publishing.service.gov.uk/media/ID/NAME`. Each file has an id of its own | Each file, whole |
| Nomis | `www.nomisweb.co.uk/output/census/2021/NAME`. One folder holds every census table | Each file, whole |
| Defra UK-AIR | `uk-air.defra.gov.uk/datastore/pcm/NAME`. One folder holds every pollutant and year | Each file, whole |
| Office for National Statistics, its website | `www.ons.gov.uk/file?uri=PATH`. The parameter names the file | Each file, whole, with its parameter |
| Ordnance Survey | `api.os.uk/downloads/v1/products/PRODUCT/downloads`, with parameters that name the area and the format | Each file, whole, with its parameters |
| Food Standards Agency | `ratings.food.gov.uk/api/open-data-files/NAME`. One file for each authority | Each file, whole |
| Greater London Authority | `data.london.gov.uk/download/DATASET/ID/NAME`. Each file has an id of its own | Each file, whole |
| HM Land Registry, UK House Price Index | `publicdata.landregistry.gov.uk/market-trend-data/house-price-index-data/NAME`. The name holds the month | Each file, whole |
| HM Land Registry, Price Paid Data | `price-paid-data.publicdata.landregistry.gov.uk/NAME`. The name holds the year, and the file of a year is replaced each month under it | Each file, whole |
| Transport for London, its website | `tfl.gov.uk/NAME`, which may be sent on. The publisher's page links an example alone, which is named nowhere | Each address whole: the one its staff wrote, and the one it may be sent on to |
| Transport for London, its store of bus data | `bus.data.tfl.gov.uk/stops-sequences/NAME`. The name holds the day, and the folder holds a folder of earlier days | Each file, whole |
| NHS England, Organisation Data Service | `www.odsdatasearchandexport.nhs.uk/api/getReport`, with a parameter that names the report | Each file, whole, with its parameter |
| NHS Business Services Authority | `opendata.nhsbsa.net/dataset/ID/resource/ID/download/NAME`. Each file has an id of its own | Each file, whole |
| Geofabrik | `download.geofabrik.de/europe/united-kingdom/england/NAME`. The folder is England's, and the name is the part of it | Each file, whole |
| Overture Maps Foundation | A file of a release of Places, by the address its own catalogue gives. The list takes a part of the one file that holds London | The one file, whole |
| Planning Data platform | `files.planning.data.gov.uk/dataset/NAME`. One folder holds every dataset of the platform, each in four formats | Each file, whole |

No file of a list is without an address, but for those a person saves. The three yearly files of Price Paid Data and the timetables of Transport for London had none until 2026-09-24, when the entry of each came to name one. To fetch a file that has none, name its address in the entry and in the list, in one change that a person reads.

Four more are saved by a person: three from a form, and the postcode directory from the publisher's portal. The entry of each names the address it was saved from before `by-hand` takes the file. The address is the one the browser recorded on the file when it was saved, with no parameter: a browser may be given an address with a key in it. It is written whole, and never as a prefix, so it names the file that was saved and no other. All four were saved on 2026-09-24. Three of the four came from a host that is not the host of the publisher's pages, and no page that was read names any of the three: `docs/research/data/by-hand-files.md` says what stands behind each.

A file that is reissued may be given a new address. Change the address under `file_urls` with the list, in a change that a person reads.

Before the field, an entry named the host of its files by an address under `evidence_urls`. The eight entries behind list m1 still hold such an address, and so do ten behind the lists `m2-places` and `m2-living`. Each says in `notes` that it is no evidence of the licence. A new entry needs none.

## What the rules on census tables cannot see

The rules read table codes: in `tables`, in an entry's id and name, and in its addresses. A code is read however it is written: with a sign in it, joined to a word, or with letters after it. A word that ends as a code does is taken for a code, because the rule cannot tell the two apart.

A table that is named with no code cannot be caught by a code: a file named for its subject, or a dataset known by a number. What catches it is the rule on addresses. A file is fetched only from an address that the entry of its source names under `file_urls`, and no entry may name an address that another entry holds. So a table about residents cannot be fetched under the entry for housing unless somebody writes its address into that entry, in a change that a person reads.

Fetch reads the names inside a zip, and inside every zip it holds. It does not read the names of the sheets of a workbook, or what is inside an archive of another kind.

The rules cannot know what a file holds. A file that mixes columns about places with columns about residents is still fenced by the conditions on its entry and by the list of columns an ingest step may read.

## A permission in writing

Some owners publish no licence that allows reuse, and give permission in a reply. No rule is made for them: the rules above already say where such a source stands.

| Part | How it is recorded |
|---|---|
| `licence` | `Bespoke-terms` |
| `conditions` | First, what was asked, who answered and on what day, and whose report that is. Then: that the permission covers what was asked and no more, that a change of use means asking again, and the credit the owner is due |
| `uses` | What was asked for, and nothing wider |
| `attribution` | Burro's wording, until the owner publishes its own. `attribution_verified` is false until then |
| The reply | It stays with whoever received it. It holds a person's name and address, so it is never saved here |
| A note | A dated note in `evidence/`, named as below. It says what was asked, by what route and on what day, what the owner answered and on what day, who has read the reply, and where it is kept. It prints no words of the reply, and holds no person's name and no address |
| `status` | `gated`, with `verified_how = "secondary_source"`, while the entry rests on a report of a reply that its writer has not read. `status_reason` says in one line what would settle it |

Six entries stand like this on 2026-09-23, for three owners: parkrun, the GIS team of the Greater London Authority, and Arts Council England. The gate refuses each for every use.

`approved` asks of such a source what it asks of any other: `verified_how = "primary_source"`, and a link under `evidence_urls`. A reply has no address that a reader can open. Whether a note in this repository can stand as that link is not decided.

## Saved evidence

`evidence/` holds dated copies of terms that are not a standard public licence, such as a marketplace's terms accepted at sign-up. It also holds the notes of a permission in writing. Name each file `<source-id>-<yyyy-mm-dd>.<ext>`.
