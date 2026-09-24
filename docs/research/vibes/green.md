# green: Green space and leafiness (London, neighbourhood scale)

Gathered on 2026-09-23. A dated snapshot, not a source of truth. Nothing here is legal advice. No file was downloaded and nothing was measured: every statement about coverage or quality is the publisher's, not a finding.

## Headline

"Leafy" can be made true to the eye with open data, but not with the dataset built for the job. The GLA's Tree Canopy Cover 2024 and Green Cover 2024 are the best maps of London's trees and both are marked "All Rights Reserved". Build on Forest Research's National Trees Outside Woodland Map instead: it is Open Government Licence v3, has a London download, and maps tree canopy over 3 m tall outside woodland. Add private outdoor space from the Indices of Deprivation 2025, which the registry already approves. Park quality has no open rating. The Green Flag list is for "personal and non-commercial use". Describe a park by what is in it and what it is designated as, not by a score.

## Summary

| The founder asked for | The engine has today | What is missing | What this research found |
|---|---|---|---|
| Leafy streets | Nothing. `leafy` is public green space, walk to a park, and low housing density | Trees outside parks: street trees, garden trees | An open canopy map of England, with a London file. Street canopy can be worked out from it |
| Parks | `green_cover`, `park_proximity`, `play_space_proximity` | How big the park is, what is in it, whether it is special | OS Open Greenspace already holds ten kinds of site. Historic England and Natural England designations are open |
| Gardens | Nothing | Private outdoor space | A new 2025 indicator, by LSOA, in a file the registry already approves |
| Park quality | Nothing | A rating | None is open. Green Flag and Fields in Trust both forbid commercial use on their sites |

Five things matter most.

1. **The GLA's 2024 canopy and green cover maps cannot be used.** Both pages show "Licence: All Rights Reserved". The GLA's own method report, read from the PDF, says the project set out to make layers that were "freely available (for further use of results)". The two do not agree. A question to the GLA GIS team may settle it.
2. **Forest Research's Trees Outside Woodland map is the open route.** It maps canopy over 3 m tall and 5 m² in area, outside woodland, for all England. Joined with the National Forest Inventory woodland map it gives total canopy. It is a first release and its accuracy in London is unmeasured.
3. **The borough tree inventory is uneven.** The GLA page says "Data varies significantly by borough (e.g., some include only highway trees; others include housing land, schools, or parks)". A count of street trees per neighbourhood would rank boroughs by what they sent in. It stays held.
4. **Private gardens have one open figure.** The Indices of Deprivation 2025 hold "Housing lacking private outdoor space" by LSOA, from Ordnance Survey and ONS data at mid-2023. It describes homes and plots, not residents. It is a score, not a share of homes, and it counts shared space for flats.
5. **Every feature proposed here describes a place.** None describes who lives there. Canopy and gardens still follow wealth, so each needs a row in the proxy audit of ADR 0006 before it ships.

## How each page was read

| Code | Meaning |
|---|---|
| B | Opened in a browser and read as text by the researcher |
| S | Read through a reader that summarises. Wording may differ from the page. Re-check before it goes in the registry |
| P | Text pulled from a PDF's text layer by a short script. Spacing was broken. Re-check any quotation |
| R | Taken from this repository's registry. Not re-opened |

## Sources

Licence is given as the page shows it. "All London" means the publisher covers every borough, not that coverage was measured.

| # | Source | Publisher | What it measures | Licence as shown | Commercial use | Finest unit | All London | Read | Proposed status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | National Trees Outside Woodland Map V1 | Forest Research, published by the Forestry Commission | Tree canopy over 3 m tall and 5 m² outside woodland: lone trees, groups, small woods | Open Government Licence, linked to v3 | Yes | Polygon | Yes, `FR_TOW_V1_London.zip` | B | approved |
| 2 | National Forest Inventory England 2024 | Forestry Commission | Woodland of 0.5 ha or more, 20 m or wider | "Open Government Licence", no version. Publisher's page says "Custom License" | Unclear | Polygon | Yes | B | gated |
| 3 | Tree Canopy Cover 2024 | Greater London Authority | Canopy from 25 cm aerial imagery, mostly 2022. London 19.6% (±0.3%) | "All Rights Reserved" | No | Polygon, in 2 km tiles. Ward and borough tables | Yes | B, P | held |
| 4 | Green Cover 2024 | Greater London Authority | All vegetation, gardens included. London 51.7% (±1.11%) | "All Rights Reserved" | No | Polygon, in 2 km tiles | Yes | B, P | held |
| 5 | London Green and Blue Cover (2019) | Greater London Authority | All vegetation and water. The GLA's 2024 page says it was based on 2016 data | Open Government Licence v3. Page adds "Contains Verisk Analytics GeoInformation Group UKMap data" | Unclear | Polygon, ward table | Yes | B | held |
| 6 | Curio Canopy (2018) | Breadboard Labs with the GLA | Canopy at 25 cm. The GLA's 2024 page says it was based on 2016 data | Creative Commons Attribution Share-Alike, linked to 4.0 | Yes, with share-alike | Polygon, LSOA, 350 m hexagon | Yes | B | held |
| 7 | London Public Realm Trees | Greater London Authority | Almost 1,140,000 public trees: place, species, some size and age | Open Government Licence v3 | Yes, with conditions | Point | No. Three boroughs lack locations. Content differs by borough | B | held, as now |
| 8 | UK ward canopy cover | Forest Research and partners | Canopy share by ward, from sampled points | Open Government Licence v3 (site footer) | Yes | Ward | Urban wards. London count not checked | S | held |
| 9 | Indices of Deprivation 2025, File 8: housing lacking private outdoor space | MHCLG | How far homes fall short of 120 m² of outdoor space at the back, 0 to 100 | Open Government Licence v3 | Yes | LSOA 2021 | Yes | P, R | approved, as now |
| 10 | Access to gardens and public green space (2020) | ONS | Share of homes with a garden, garden size | Open Government Licence v3 | Yes | MSOA | Yes | S | none: superseded by 9 |
| 11 | OS Open Greenspace | Ordnance Survey | Public green sites and their entrances, in ten kinds | Open Government Licence v3 | Yes | Polygon and point | Yes | R, S | approved, as now |
| 12 | Historic parks and gardens | Historic England, on the MHCLG Planning Data platform | Register of Parks and Gardens of Special Historic Interest, 1,723 in England | "Licensed under the Open Government Licence v.3.0" | Yes, with conditions | Polygon | Yes. London count not measured | B | approved |
| 13 | Local nature reserves | Natural England and MHCLG, on the Planning Data platform | 1,731 statutory local nature reserves | "Licensed under the Open Government Licence v.3.0" | Yes | Polygon | Yes. London count not measured | B | approved |
| 14 | Ancient woodland, national nature reserves, SSSIs | Natural England, on the Planning Data platform | Designated sites | Open Government Licence v3 | Yes | Polygon | Yes | S | gated |
| 15 | Country Parks (England) | Natural England | Boundaries of country parks | "Open Government Licence", no version | Unclear | Polygon | Not measured | S | none: low priority |
| 16 | Green Flag Award winners | Keep Britain Tidy | Parks and green spaces judged to be well managed. Owners apply | Site terms: "personal and non-commercial use" | No | Site | Yes | B | held |
| 17 | Green Space Index | Fields in Trust | Green space provision and walking distance | Site terms forbid commercial use without a licence | No | Region on the page read | Not at neighbourhood scale | S | held |
| 18 | Good Parks for London | Parks for London | How each borough's parks service performs | "© Parks for London 2026" | Unclear | Borough | Borough only | S | none: too coarse |
| 19 | Tree Equity Score UK | American Forests, Woodland Trust, Centre for Sustainable Healthcare | A score mixing canopy with income, age, health, heat and air | None found | Unclear | LSOA | Yes | S | held |
| 20 | Trees map | Friends of the Earth with Terra Sulis | Canopy share by LSOA | None found | Unclear | LSOA | Yes | S | none: no licence |
| 21 | Green and Blue Infrastructure (England) | Natural England | Accessible green space analysis | "Open Government Licence". Credits the National Trust, Sport England and five wildlife trusts | Unclear | LSOA | Yes | S | none: mixed rights |
| 22 | ESA WorldCover 2021 | European Space Agency | Land cover in 11 classes | Creative Commons Attribution 4.0 | Yes | 10 m pixel | Yes | S | gated |
| 23 | High Resolution Canopy Height Maps | Meta and World Resources Institute | Canopy height from satellite imagery | Creative Commons Attribution 4.0 | Yes | About 1 m (not confirmed) | Yes | S | none: imagery date unclear |
| 24 | Urban Atlas Street Tree Layer 2018 | Copernicus Land Monitoring Service | Street trees in European cities. Only the title was read | Copernicus data policy: free, full and open | Yes | Polygon | Not confirmed | S | none: coverage not confirmed |
| 25 | Trees and tree preservation zones | Local planning authorities, on the Planning Data platform | Trees under a preservation order | Open Government Licence v3 | Yes | Point and polygon | No. 78 and 82 providers in England | S | none: incomplete |
| 26 | London Parks and Gardens Inventory | London Gardens Trust | Over 2,500 historic green sites | None stated | Unclear | Site | Yes | S | none: link out only |
| 27 | GiGL open space data | Greenspace Information for Greater London | Open space, nature sites | Commercial use not permitted | No | Polygon | Yes | R | banned, as now |

## Which can be had for all of London at neighbourhood scale

| Need | Best open source | All London | Finest unit | Verdict |
|---|---|---|---|---|
| Tree canopy | 1 and 2 together | Yes | Polygon | Yes. Quality in London unmeasured |
| Trees along streets | 1, with OS Open Roads | Yes | Polygon and centre line | Probably. Needs a spike: see below |
| Count of street trees | 7 | No | Point | No. Boroughs sent different things |
| All vegetation, gardens included | 22 | Yes | 10 m pixel | Roughly. Too coarse to see a street tree |
| Private outdoor space | 9 | Yes | LSOA | Yes, as a score |
| Parks: place, size, kind | 11 | Yes | Polygon | Yes |
| Parks: designation | 12, 13, 14 | Yes | Polygon | Yes |
| Parks: quality rating | None | | | No |
| Anything at borough scale | 18 | | Borough | No. A borough figure says little about a neighbourhood |

## What could be built

### Features

Every one describes a place or its buildings. None describes residents.

| Proposed `feature_id` | Label | From | How | Describes | Honest limits |
|---|---|---|---|---|---|
| `canopy_cover` | Tree canopy as a share of the area | 1, 2 | Sum canopy area per Output Area, roll up | Place | Trees under 3 m are missed. Height data dates from 2017 to 2024, so new planting and felling are missed. First release |
| `street_canopy` | Share of street length with tree canopy within 10 m | 1, 2, OS Open Roads | Buffer each local street, measure canopy inside | Place | The map used OS MasterMap so that "buildings and roads are removed". Canopy over the carriageway may be cut away. Unproven until the spike |
| `private_outdoor_space` | Private outdoor space at homes | 9 | LSOA shortfall score, weighted by count of homes. A lower score means more outdoor space | Buildings and plots | A 0 to 100 score after shrinkage, not a share of homes. Shared space counts for flats. Balconies are not counted. Front gardens are not counted |
| `park_large_proximity` | Walk to the nearest park of 20 ha or more | 11 | As `park_proximity`, with a higher floor | Place | Size says nothing of upkeep. Woodland and commons are outside this product |
| `park_facilities` | Kinds of facility within a 15-minute walk | 11 | Count distinct kinds: play space, tennis court, bowling green, playing field, other sports facility, allotments | Place | Presence only. Not condition, not opening hours, not cost |
| `historic_park_proximity` | Walk to the nearest registered historic park or garden | 12 | Network distance to an entrance, or to the edge if none | Place | Some registered gardens are private. Check access against 11 |
| `nature_reserve_proximity` | Walk to the nearest local or national nature reserve | 13, 14 | As above | Place | A designation, not a promise of access |
| `vegetation_cover` | Vegetation as a share of the area | 22 | Share of 10 m pixels in the vegetation classes | Place | 10 m pixels. 2021. The class list was not read. Hold until the GLA answers on source 4 |

### Tags

| Tag | Today | Proposed | Why |
|---|---|---|---|
| `leafy` | 0.45 `green_cover` high + 0.30 `park_proximity` low + 0.25 `homes_density` low | 0.35 `canopy_cover` high + 0.30 `street_canopy` high + 0.20 `green_cover` high + 0.15 `private_outdoor_space` low, which is less shortfall | Low density stands in for trees today. Measure the trees |
| `parks_close_by` (new) | | 0.35 `park_proximity` low + 0.25 `park_large_proximity` low + 0.25 `park_facilities` high + 0.15 `historic_park_proximity` low | "Leafy" and "near a good park" are different wishes. Today one tag carries both |

Weights are a starting point. A tag ships only if it passes the 40-neighbourhood sanity set. Changing `leafy` changes the contract and `CATALOGUE_VERSION`. That is for the team that owns `packages/core`.

### Experience

| Idea | What it needs | Rule it touches |
|---|---|---|
| Three lines on every area page: streets, parks, gardens. Each with its figure, source and date | The features above | None |
| A canopy layer on the map, so "leafy" can be seen and not only read | Source 1 registered for `display` | None |
| "Nearest large park: {name}, about {walk} minutes on foot, {hectares} ha" | A new fact kind, like `station`, with the park's name in `names` | PLAN section 4 leaves named venues out of v1. A park is not a venue, but it is a name. Founder decides |
| Separate words in the prompt reader: "tree-lined", "park", "garden", "woods", "allotment", "playground" | Rules vocabulary | None |
| A missing figure says so | Already the rule | None |

### Order of work

| Step | What | Done when |
|---|---|---|
| 1 | Read the accuracy report that ships with source 1 | Its urban accuracy is written in the registry entry |
| 2 | Spike: load the London file. Check whether canopy meets the road edge on 20 streets that people who know London call tree-lined, and 20 they do not | `street_canopy` separates the two lists, or is dropped |
| 3 | Compare London-wide canopy from 1 and 2 with the GLA's published 19.6% | The gap is known and written down |
| 4 | Open File 8 and find the outdoor space column | Its form, score or rank, is known |
| 5 | Put the two questions below to their owners | Both are asked |

## What cannot be done honestly

| Claim | Why not |
|---|---|
| "This street is tree-lined" | No open source is reliable at the scale of one street. Say it of an area, as a share |
| A park quality score | No open rating exists. Green Flag is an award that a park's owner applies for, and a park that did not apply is not a worse park |
| "Green Flag parks nearby" | The site grants "the right to access the Website for your personal and non-commercial use" and bars copying or derived works |
| Street trees per kilometre, compared across London | Borough inventories differ in what they hold. Three boroughs have no locations for some or all records |
| Tree species, blossom, autumn colour | Only in the borough inventories, with the same gaps |
| "Most homes here have a garden" | The open figure is a shortfall score by LSOA. It is not a share of homes. It counts shared space for flats and cannot see a balcony |
| How green a named home or street is | Area figures only. The registry says the same of flood risk |
| Canopy "today" | Source 1 spans 2017 to 2024. Say the span |
| A borough figure shown as a neighbourhood fact | Sources 17 and 18 are regional or borough level |
| Greenery from street photographs | Google Street View is banned. Mapillary is share-alike and held |
| Nature sites and "areas of deficiency" from GiGL | Banned |
| "Well kept", "quiet", "safe" of a park | No data. The verifier bans "safe" in any case |
| Green cover with gardens, at fine scale | Source 4 does it and is not licensed. Source 22 is open and coarse |

## What the founder must decide

| # | Decision | Choices | What each allows and risks | Recommendation |
|---|---|---|---|---|
| 1 | Ask the GLA about sources 3 and 4? | Ask. Do not ask | A yes gives the best canopy and the only fine map of gardens and verges. The imagery came from a commercial supplier, so the answer may be no. Asking costs little | Ask the GLA GIS team. Quote the method report's "freely available (for further use of results)". Build on source 1 meanwhile |
| 2 | Write to Keep Britain Tidy for the Green Flag list? | Write. Do without | A yes gives the one park standard people know. It covers only parks whose owners chose to apply, so it says as much about the owner as the park | Write, and ask for names and locations only. Ship without it |
| 3 | Rebuild `leafy` on measured canopy? | Keep today's formula. Replace it | Replacing it makes the tag match what people see. It depends on a first-release dataset | Replace, after steps 1 to 3 pass |
| 4 | Is private outdoor space a place fact? | Yes, rank on it. Show only. Leave out | It describes plots, which ADR 0006 allows. It comes from a deprivation index and follows wealth. Its form is a score that is hard to say in a sentence | Yes, with a proxy audit row. Never show it under the word "deprivation" |
| 5 | Name parks on area pages? | Name them. Counts and distances only | Names make a page feel like a place. Each name needs a fact and a source, and a wrong name is seen at once | Name the nearest large park only, from source 11, once its name field has been checked |
| 6 | Show the borough tree inventory at all? | As a map layer with a warning. Not at all | People like seeing individual trees. Gaps would read as "no trees here" | Not at all in v1 |
| 7 | Use a 10 m satellite product for vegetation? | Use source 22 now. Wait for source 4 | Source 22 is open and even across London. It cannot see a street tree or a small garden | Wait. `canopy_cover` and `green_cover` carry the tag without it |
| 8 | Proxy audit rows for canopy and gardens | Write them before ingest. After | Forest Research's page on its ward data says "Wards with low canopy cover were more likely to be deprived in England" (read through the reader that summarises) | Before. ADR 0006 asks for the rule before the audit runs |

## What this research turned up about entries already in the registry

For whoever owns `registry/`. Nothing was edited.

| Entry | Finding | Read |
|---|---|---|
| `gla-public-realm-trees` | The page now says the data is "collated by GiGL". Its "tree location type" was set using "Ordnance Survey MasterMap Topography" and "GiGL's Open Space Dataset". GiGL's own data is banned here. Ask the GLA whether the licence covers that column, or drop it at ingest | B |
| `gla-public-realm-trees` | The newest file is `Public_Realm_tree_list_2025_November.csv`. Update frequency is "On request". Bromley's records were kept from an earlier round | B |
| `historic-england-listed-buildings` | The parks and gardens page on the same platform shows two more sentences of attribution than this entry records, starting "The Historic England GIS Data contained in this material was obtained on [date]". The listed building page was not re-opened. Worth a look | B |
| `os-open-greenspace` | The ten kinds of site were confirmed from the code list: Allotments or Community Growing Spaces, Bowling Green, Cemetery, Religious Grounds, Golf Course, Other Sports Facility, Play Space, Playing Field, Public Park or Garden, Tennis Court | S |
| `mhclg-iod-2025-underlying-indicators` | The outdoor space indicator rests on "a bespoke extract of property-level data provided by OS and ONS". The entry already asks for the notes sheet of File 8 to be read for third-party copyright. That check matters more now | P |

## What was not read

- **Web search.** None was made. Every page was reached by a known or guessed address. Sources nobody links to from those pages will have been missed.
- **Any data file.** Nothing was downloaded. Coverage, accuracy and field names are the publishers' words.
- **The accuracy report for source 1.** It sits behind a download button. Its urban accuracy is unknown to this report.
- **Whether source 1 cuts canopy at the road edge.** The page says roads "are removed". What that does to a street tree's crown is not stated.
- **The licence details for source 2.** The publisher's page shows "Custom License" with a link that was not opened.
- **PDFs.** The GLA method report and the deprivation technical report were read by pulling text from the file. Quotations from them need checking against the page.
- **File 8 itself.** Whether the outdoor space indicator is published as a score, a rank or both is not confirmed.
- **OS Open Greenspace exclusions and name field.** The overview page did not state what is left out, nor whether every site carries a name.
- **Keep Britain Tidy's own terms page.** Not read. The Green Flag site's terms were read in full, and they name Keep Britain Tidy as the owner.
- **Tree Equity Score method page.** Not read. The home page was read through the reader that summarises. It says canopy is "derived from pre-aggregated Google high-resolution tree canopy".
- **Urban Atlas coverage of London.** The product page was not read.
- **Natural England's and Historic England's own sites.** Not opened. Their data was read from the copies on the Planning Data platform.
- **Paid products.** OS MasterMap Greenspace and the commercial tree maps were not priced or read. No claim is made about their terms.
- **Counts for London.** How many registered parks, nature reserves or wards fall in London was not measured.
- **Fields in Trust at finer scale.** The page read showed regions only. Whether the tool holds smaller areas is unknown, and the terms rule it out either way.

## Proposed registry entries

In the registry's own format. Not added to the registry. Each entry names the file it would sit in. `attribution_verified` is true only where the wording was read in a browser.

```toml
# For registry/sources/environment.toml

[[source]]
id = "forest-research-trees-outside-woodland-v1"
name = "National Trees Outside Woodland Map (TOW) V1"
publisher = "Forest Research, published by the Forestry Commission"
url = "https://environment.data.gov.uk/dataset/9c41b3c6-2453-44f6-9900-e7821f1a1072"
dimension = "environment"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "© Forestry Commission copyright and/or database right 2025. All rights reserved."
attribution_verified = true
conditions = [
    "The map leaves out woodland in the National Forest Inventory. Total canopy needs both.",
    "Trees under 3 m and canopy under 5 m² are not mapped. Do not describe it as every tree.",
    "The period is 1 January 2017 to 31 December 2024. Show the span wherever a figure appears.",
    "The publisher says objects missing from OS mapping may be misclassified, and names static caravans, shipping containers, large tents, marquees, coastal cliffs and solar farms.",
    "The publisher calls it a first release and says the method will be reviewed. Re-check at each new version.",
    "Area-level use only. Never state the tree cover of one home or one street.",
]
status = "approved"
before_launch = [
    "Read TOW_RELEASE_V1_NCEA_Report.pdf and record its accuracy for urban land.",
    "Measure the London file: does canopy reach the road edge, and does the London total sit near the GLA's published 19.6%?",
]
uses = ["scoring", "display"]
cadence = "As needed. Published 1 April 2025, revised 24 April 2025."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://environment.data.gov.uk/dataset/9c41b3c6-2453-44f6-9900-e7821f1a1072",
    "https://www.forestresearch.gov.uk/tools-and-resources/fthr/trees-outside-woodland-tow-projects/trees-outside-woodland-map/",
]
notes = "How it was verified: both pages were opened in a browser on 2026-09-23. The Defra Data Services Platform page shows 'Licence: Open Government Licence', linked to version 3, the attribution statement above, and 'There are no public access constraints to this data'. Forest Research's page says 'The TOW map is available under open government licence and free to download'. Inputs named by the publisher: National Lidar Survey and Vegetation Object Model (Environment Agency), Sentinel-2, OS MasterMap. London file: FR_TOW_V1_London.zip. No file was opened."

[[source]]
id = "forestry-commission-national-forest-inventory-england-2024"
name = "National Forest Inventory England 2024 (woodland map)"
publisher = "Forestry Commission"
url = "https://data-forestry.opendata.arcgis.com/datasets/d62fd97664a64596844b9834c1737e46_0/about"
dimension = "environment"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "unknown"
share_alike = false
attribution = "© Forestry Commission copyright and/or database right 2025. All rights reserved."
attribution_verified = false
conditions = [
    "Woodland of 0.5 ha or more only. It includes felled and newly planted land, and open land inside woods. Filter to standing woodland before counting canopy.",
]
status = "gated"
status_reason = "Wanted beside the Trees Outside Woodland map. The data.gov.uk record says 'Open Government Licence' with no version. The publisher's own page shows 'Custom License' with details that were not opened. Gate: open 'View license details' on the publisher's page, confirm version 3, save it."
uses = ["prototyping_only"]
cadence = "Annual"
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.data.gov.uk/dataset/05f053ef-4298-42b7-a20a-2476c5f749d7/national-forest-inventory-england-2024",
    "https://data-forestry.opendata.arcgis.com/datasets/d62fd97664a64596844b9834c1737e46_0/about",
]
notes = "Both pages opened in a browser on 2026-09-23. The attribution statement is from the data.gov.uk record's summary. 361,039 records."

[[source]]
id = "natural-england-local-nature-reserves"
name = "Local nature reserves"
publisher = "Natural England and the Ministry of Housing, Communities and Local Government (copy published on the Planning Data platform)"
url = "https://www.planning.data.gov.uk/dataset/local-nature-reserve"
dimension = "environment"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "© Crown copyright and database right 2026"
attribution_verified = true
conditions = [
    "Approval covers only the copy on planning.data.gov.uk.",
    "The page says it 'Contains some data created by MHCLG'. Keep the per-record provider.",
    "A designation is not a promise of public access. Check against OS Open Greenspace before saying a person can walk in.",
    "Update the year in the statement to match the data used.",
]
status = "approved"
uses = ["scoring", "display"]
cadence = "Collector runs daily. New data last found 2026-08-20."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://www.planning.data.gov.uk/dataset/local-nature-reserve"]
notes = "Opened in a browser on 2026-09-23. 1,731 records for England. London count not measured."

[[source]]
id = "natural-england-ancient-woodland"
name = "Ancient woodland"
publisher = "Natural England (copy published on the Planning Data platform)"
url = "https://www.planning.data.gov.uk/dataset/ancient-woodland"
dimension = "environment"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "© Natural England copyright. Contains Ordnance Survey data © Crown copyright and database right 2026."
attribution_verified = false
status = "gated"
status_reason = "Read through a reader that summarises only. Gate: open the page in a browser and confirm the licence and the attribution wording. The same gate applies to the national nature reserve and SSSI datasets on the same platform, which need their own entries if used."
uses = ["prototyping_only"]
cadence = "Collector runs daily. New data last found 2026-03-21."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://www.planning.data.gov.uk/dataset/ancient-woodland"]

[[source]]
id = "gla-tree-canopy-cover-2024"
name = "Tree Canopy Cover 2024"
publisher = "Greater London Authority"
url = "https://data.london.gov.uk/dataset/tree-canopy-cover-2024-2w4m3"
dimension = "environment"
licence = "None-stated"
commercial_use = "no"
share_alike = false
attribution = "Not applicable. Not ingested."
attribution_verified = false
conditions = [
    "Do not download, open or ingest the map layer or the ward and borough tables.",
    "The London-wide figure printed on the page may be read as a published fact when checking other data. It must not be shown in the product.",
]
status = "held"
status_reason = "The dataset page shows 'Licence: All Rights Reserved' (opened in a browser on 2026-09-23). The method report says the project set out to make layers that were 'freely available (for further use of results)'. Its imagery and height data came from a commercial supplier and it uses OS MasterMap. A written licence from the GLA GIS team settles it."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://data.london.gov.uk/dataset/tree-canopy-cover-2024-2w4m3"]
notes = "Imagery mostly 2022, some 2021 and 2020, April to October. 467 shapefile tiles of 2 km. Maintainer: GLA GIS. Update frequency: one off. The registry has no value for 'All Rights Reserved', so licence is 'None-stated': no licence is granted."

[[source]]
id = "gla-green-cover-2024"
name = "Green Cover 2024"
publisher = "Greater London Authority"
url = "https://data.london.gov.uk/dataset/green-cover-2024-e56n0"
dimension = "environment"
licence = "None-stated"
commercial_use = "no"
share_alike = false
attribution = "Not applicable. Not ingested."
attribution_verified = false
conditions = ["Do not download, open or ingest the map layer or the ward and borough tables."]
status = "held"
status_reason = "The dataset page shows 'Licence: All Rights Reserved' (opened in a browser on 2026-09-23). The page says the model is 'supplemented' with 'categories from the Ordnance Survey MasterMap Topography Layer'. A written licence from the GLA GIS team settles it. Ask with gla-tree-canopy-cover-2024."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://data.london.gov.uk/dataset/green-cover-2024-e56n0"]

[[source]]
id = "gla-green-and-blue-cover-2019"
name = "London Green and Blue Cover"
publisher = "Greater London Authority"
url = "https://data.london.gov.uk/dataset/london-green-and-blue-cover-emqzm"
dimension = "environment"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes_with_conditions"
share_alike = false
attribution = "Contains OS data © Crown copyright and database rights 2019. Contains Verisk Analytics GeoInformation Group UKMap data."
attribution_verified = true
conditions = [
    "The page says the layer contains a commercial company's map data. An Open Government Licence cannot grant rights the GLA does not hold. Ask the GLA before any use that reaches a user.",
    "Imagery is from 2016. Ten years old at launch.",
    "London Datastore site terms: state that the Greater London Authority cannot warrant the quality or accuracy of the data, and do not imply endorsement.",
]
status = "held"
status_reason = "Old, and carries third-party data. Kept for checking other sources only. A written reply from the GLA that the licence covers the whole layer would allow promotion, though newer data should be preferred."
uses = ["validation_only"]
cadence = "One off"
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://data.london.gov.uk/dataset/london-green-and-blue-cover-emqzm"]
notes = "Opened in a browser on 2026-09-23. The page also says: 'The data is based on Ordnance Survey mapping and the data is published under Ordnance Survey's presumption to publish'."

[[source]]
id = "breadboard-labs-curio-canopy-2018"
name = "Curio Canopy: London Tree Canopy Cover"
publisher = "Breadboard Labs, with the Greater London Authority"
url = "https://data.london.gov.uk/dataset/curio-canopy-london-tree-canopy-cover-2koz8"
dimension = "environment"
licence = "CC-BY-SA-4.0"
licence_url = "https://creativecommons.org/licenses/by-sa/4.0/"
commercial_use = "yes_with_conditions"
share_alike = true
attribution = "Curio Canopy, Breadboard Labs and the Greater London Authority, CC BY-SA 4.0"
attribution_verified = false
conditions = [
    "Share-alike. It can never feed scoring or the gazetteer.",
    "Imagery is from 2016.",
]
status = "held"
status_reason = "Share-alike keeps it out of scoring, and newer canopy data exists. Kept so that nobody picks it up by mistake."
uses = ["validation_only"]
cadence = "One off"
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://data.london.gov.uk/dataset/curio-canopy-london-tree-canopy-cover-2koz8"]
notes = "Opened in a browser on 2026-09-23. The attribution is this report's wording, not the publisher's."

[[source]]
id = "forest-research-uk-ward-canopy-cover"
name = "UK urban canopy cover by ward"
publisher = "Forest Research, with Trees for Cities, Brillianto and the Woodland Trust"
url = "https://www.forestresearch.gov.uk/research/i-tree-eco/uk-urban-canopy-cover/"
dimension = "environment"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "Contains public sector information licensed under the Open Government Licence v3.0."
attribution_verified = false
conditions = [
    "Estimates from sampled points, gathered by volunteers. Each has a margin of error.",
    "Ward boundaries do not match Burro's neighbourhoods.",
]
status = "held"
status_reason = "Useful only to check canopy worked out from the Trees Outside Woodland map. The licence is the site footer's, read through a reader that summarises. The download page was not opened."
uses = ["validation_only"]
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://www.forestresearch.gov.uk/research/i-tree-eco/uk-urban-canopy-cover/"]

[[source]]
id = "esa-worldcover-2021"
name = "ESA WorldCover 2021 (10 m land cover)"
publisher = "European Space Agency"
url = "https://esa-worldcover.org/en/data-access"
dimension = "environment"
licence = "CC-BY-4.0"
licence_url = "https://creativecommons.org/licenses/by/4.0/"
commercial_use = "yes"
share_alike = false
attribution = "© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium"
attribution_verified = false
conditions = [
    "10 m pixels. Do not use it to say anything about a street or a garden.",
    "The basemap already carries a landcover layer derived from WorldCover. That is a separate use under the basemap entry.",
]
status = "gated"
status_reason = "A fallback for total vegetation if the GLA says no. Read through a reader that summarises only. Gate: open the licence page in a browser, and show in a spike that 10 m pixels rank London neighbourhoods sensibly."
uses = ["prototyping_only"]
cadence = "2020 and 2021 editions"
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://esa-worldcover.org/en/data-access"]

[[source]]
id = "keep-britain-tidy-green-flag-award-winners"
name = "Green Flag Award winners"
publisher = "Keep Britain Tidy"
url = "https://www.greenflagaward.org/award-winners/"
dimension = "environment"
licence = "Bespoke-terms"
licence_url = "https://www.greenflagaward.org/terms-conditions/"
commercial_use = "no"
share_alike = false
attribution = "Not applicable. Not ingested."
attribution_verified = false
conditions = [
    "Do not copy the list from the website, by hand or by script.",
    "If a licence is granted: an award is applied for. A park with no award is not a worse park. Say so wherever it is shown.",
]
status = "held"
status_reason = "The site's terms, clause 2.3: 'We grant you the right to access the Website for your personal and non-commercial use.' Clause 2.4 bars copying and derived works. Opened in a browser on 2026-09-23. A written licence from Keep Britain Tidy for the names and locations of winning sites settles it."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://www.greenflagaward.org/terms-conditions/"]
notes = "The terms say the website 'is run and hosted by Keep Britain Tidy' and that the scheme 'is managed on behalf of The Department for Communities and Local Government'. The winners page is a map with a search box. No download was seen."

[[source]]
id = "fields-in-trust-green-space-index"
name = "Green Space Index"
publisher = "Fields in Trust"
url = "https://fieldsintrust.org/insights/green-space-index"
dimension = "environment"
licence = "Bespoke-terms"
licence_url = "https://fieldsintrust.org/terms-of-use"
commercial_use = "no"
share_alike = false
attribution = "Not applicable. Not ingested."
attribution_verified = false
status = "held"
status_reason = "The site's terms say: 'You must not use any part of the materials on our site for commercial purposes without obtaining a license to do so from us or our licensors.' Read through a reader that summarises on 2026-09-23. The page read showed regional figures only, which say little about a neighbourhood. A licence and a finer geography would both be needed."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://fieldsintrust.org/terms-of-use",
    "https://fieldsintrust.org/insights/green-space-index",
]

[[source]]
id = "american-forests-tree-equity-score-uk"
name = "Tree Equity Score UK"
publisher = "American Forests, the Woodland Trust and the Centre for Sustainable Healthcare"
url = "https://uk.treeequityscore.org/"
dimension = "environment"
licence = "None-stated"
commercial_use = "unknown"
share_alike = false
attribution = "Not applicable. Not ingested."
attribution_verified = false
conditions = [
    "The score mixes canopy with income, age and health. Under ADR 0006 it could not feed ranking or a tag even if it were licensed.",
]
status = "held"
status_reason = "No licence was found. The home page says canopy is 'derived from pre-aggregated Google high-resolution tree canopy'. The terms of that input were not read. Read through a reader that summarises on 2026-09-23. The method page was not read."
verified_how = "unverified"
verified_on = 2026-09-23
evidence_urls = ["https://uk.treeequityscore.org/"]

# For registry/sources/heritage.toml

[[source]]
id = "historic-england-registered-parks-and-gardens"
name = "Register of Parks and Gardens of Special Historic Interest"
publisher = "Historic England (copy published on the MHCLG Planning Data platform)"
url = "https://www.planning.data.gov.uk/dataset/park-and-garden"
dimension = "heritage"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes_with_conditions"
share_alike = false
attribution = "© Historic England 2026. Contains Ordnance Survey data © Crown copyright and database right 2026. The Historic England GIS Data contained in this material was obtained on [date]. The most publicly available up to date Historic England GIS Data can be obtained from HistoricEngland.org.uk."
attribution_verified = true
conditions = [
    "Approval covers only the copy on planning.data.gov.uk.",
    "Fill '[date]' with the day the data was fetched. Update the years to match.",
    "The page says it 'Contains some data created by MHCLG'. Keep the per-record provider.",
    "Some registered gardens are private. Check access against OS Open Greenspace before saying a person can visit.",
]
status = "approved"
uses = ["scoring", "display"]
cadence = "Collector runs daily. New data last found 2026-09-23."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://www.planning.data.gov.uk/dataset/park-and-garden"]
notes = "Opened in a browser on 2026-09-23. 1,723 records for England. London count not measured. Historic England's own site was not opened."
```
