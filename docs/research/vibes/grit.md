# grit: crime, the street, and deprivation (London, neighbourhood scale)

Researched 2026-09-23. A dated snapshot, not a source of truth. Nothing here is legal advice. No lawyer has read it.

## Headline

"Gritty" as the founder described it has three parts: crime, socioeconomic factors and street cleanliness. Only the first can be measured honestly at neighbourhood scale today. No open dataset measures how clean a London street is below borough level. The socioeconomic part describes residents, and the official deprivation indicators behind it include English language ability, asylum support and disability benefits, so it cannot enter a tag while ADR 0006 stands. What can be built is two things side by side: a **street character scale** from land use, main roads, noise and built form, which a person can seek at either end, and **street incidents** (recorded criminal damage and anti-social behaviour) shown by category under the crime rules Burro already has. A file the registry already approves holds the incident rates and the noise figure for all 4,994 London LSOAs. The scale also needs an official land use table, which is under OGL v3 and has not yet been opened.

## Summary

| The founder asked for | The engine has today | What this research found |
|---|---|---|
| Crime in "gritty" | Two crime features, off by default, in no tag | Eight recorded-crime rates by LSOA are already in an approved file, criminal damage and anti-social behaviour among them. Nobody had opened it. I did |
| Socioeconomic factors | Nothing, by rule | The deprivation domains for income, employment, education and health describe residents. Two of the other three are mixed. Only single indicators are safe, never a domain score |
| Street cleanliness | Nothing | No open source below borough level. Fly-tipping is per borough. The national litter survey is national only and last ran for 2018 to 2019. FixMyStreet's publisher says its data must not be used to rank areas |
| "Gritty" as a relatable word | 12 tags, none of them a quality some people avoid | A scale with "polished" at the other end works, but only if nothing on it is a nuisance. Nobody seeks criminal damage |
| Vacant shops, betting shops, late licences, graffiti | Nothing | Vacancy is members-only. The betting register's terms conflict. Late licences are per borough. No graffiti or street art data was found |
| Industrial land, traffic | Nothing | Official land use by LSOA exists under OGL v3, as at April 2022. Road class is in an approved source |

Six things matter most.

1. **"Seekable grit" and "crime-based grit" are two different products.** The contract gives a nuisance one direction: a person can ask for less of it, never more. If crime sits inside "gritty", a person who asks for a gritty area is asking Burro to rank up recorded crime. So the scale that people seek must be built without crime, and crime must sit beside it.
2. **The approved deprivation file is richer than the registry says.** File 8 of the Indices of Deprivation 2025 publishes eight crime rates, noise, air quality, road casualties, outdoor space and energy performance for every London LSOA. The registry entry names noise only. Using the others is a change to the feature catalogue, not to a licence.
3. **Recorded criminal damage moves with recorded violence.** Across London's 4,994 LSOAs, the rank correlation between criminal damage and violence with injury is 0.81. A tag built on criminal damage would rank areas much as a violence figure does. Noise is a different thing: its correlation with criminal damage is 0.19.
4. **A deprivation domain score cannot be split after the fact.** The Living Environment score mixes noise with a housing condition model that uses occupant characteristics. The Barriers score mixes travel time with overcrowding and homelessness. Take indicators, never scores.
5. **Borough figures say little about a neighbourhood.** London has 33 local authorities and Burro ranks about 450 neighbourhoods. A borough figure gives every neighbourhood in the borough the same value. Fly-tipping and alcohol licensing are both borough figures. Neither should be scored or shown as a neighbourhood fact.
6. **Every place-based feature here will still follow deprivation.** Industrial land, main roads and takeaways are not spread evenly. Each needs a row in the proxy audit of ADR 0006 before it ships. I did not run any correlation against data about residents, because ADR 0006 asks for the written rule first.

How this was done, and its limits:

- No web search was made. Every page was reached by a known or guessed address, or through a publisher's own search page. **Sources I did not already know of may be missing.**
- Most pages were read through a reader that summarises. Quoted wording must be re-checked in a browser before it goes into the registry as `attribution_verified = true`.
- Three files were opened. The Indices of Deprivation technical report (a PDF) was read as text pulled out by a short script. File 8 of the Indices, which the registry approves, was opened with a script: its sheet names, column headers and notes sheet were read, and its London rows were counted. The London Fire Brigade's metadata sheet (12 kB, a list of field names) was read in full.
- No data file from an unregistered source was opened. The fire brigade's metadata sheet is a list of fields, not data. That is why the land use table and the fire incident files are described from their pages, not from their contents.
- The copy of File 8 was deleted afterwards. Nothing was added to the repository but this report.

## How each page was read

| Code | Meaning |
|---|---|
| S | Read through a reader that summarises. Wording may differ from the page |
| V | The reader was asked for the text word for word. Closer than S, and still to be re-checked |
| P | Text pulled from a PDF by a short script. Spacing was broken in places |
| F | The file itself was opened with a script |
| R | Taken from this repository's registry. Not re-opened today |

## Sources

"Describes" says what the data is about: a place, events in a place, buildings, or residents. "Status" is the status in the registry today, or the one proposed at the end of this report.

| # | Source | Publisher | What it measures | Describes | Licence as shown | Commercial use | Finest unit | All London | Read | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Street-level crime and anti-social behaviour | data.police.uk | Recorded crime in 14 categories and ASB, monthly | Events in a place | OGL v3 | Yes | Anonymised point, with LSOA code | Yes, with gaps by force and month | R, S | approved, as now |
| 2 | Indices of Deprivation 2025, File 8: underlying indicators | MHCLG | 8 crime rates, noise, air quality, road casualties, outdoor space, energy performance, housing condition, travel time, and resident indicators | Mixed, by indicator. See the section below | OGL v3 | Yes | LSOA 2021 | Yes: 4,994 of 4,994 have a value in every column checked | F, P, S | approved, as now |
| 3 | Indices of Deprivation 2025, Files 1 to 7 and 9: ranks, deciles, domain and sub-domain scores | MHCLG | Composite scores | Residents, or mixed | OGL v3 | Yes | LSOA 2021 | Yes | S | not registered. Propose no product entry |
| 4 | Food Hygiene Rating Scheme | Food Standards Agency | Food businesses by type. Types include "Takeaway/sandwich shop" and "Pub/bar/nightclub" | Place | OGL v3 | Yes, with conditions | Point | Yes | R, S | approved, as now |
| 5 | OS Open Roads | Ordnance Survey | Road links by class | Place | OGL v3 | Yes | Line | Yes | R | approved, as now |
| 6 | Land use statistics: England 2022, table P405 | DLUHC, now MHCLG | Land in 28 categories, among them industry, storage and warehousing, landfill and waste, vacant land | Place | OGL v3 | Yes | LSOA, vintage not stated | Yes, by the publisher's account | S | gated (new) |
| 7 | London Fire Brigade Incident Records | London Fire Brigade, hosted by the GLA | Every incident attended since 2009, with type and property type | Events in a place | OGL v2 | Yes, with conditions | Coordinates rounded to 50 m | Yes | S, F (metadata only) | gated (new) |
| 8 | Brownfield land | MHCLG Planning Data platform | Sites that planning authorities judge suitable for housing | Place | "Licensed under the Open Government Licence v.3.0" | Yes | Site | Not measured. The page says the data "may be incomplete" | S | held (new) |
| 9 | Road traffic counts | Department for Transport | Annual average daily flow at count points, to 2025 | Place | OGL v3 | Yes | Count point | Major roads well, minor roads by sample | S, R | held, as now |
| 10 | Strategic Noise Mapping Round 4 | Defra | Modelled road and rail noise, 2021 | Place | OGL v3 | Yes | Grid | Yes | R. The page was not read today | held, as now |
| 11 | Road safety data (STATS19) | Department for Transport | Injury collisions | Events in a place | OGL v3 | Yes | Point | Yes | R | held, as now |
| 12 | Fly-tipping statistics for England | Defra | Incidents councils recorded, and actions taken | Place, by whole borough | OGL v3 | Yes | Local authority | Borough only | S | held (new): too coarse |
| 13 | Litter and littering in England: data dashboard | Defra | Site cleanliness from a survey of sites in 42 volunteer councils | Place | OGL v3 | Yes | England only | No | S | none: national only, last edition 2018 to 2019 |
| 14 | FixMyStreet Geographic Counts | mySociety | Reports of street problems by LSOA and local authority | Reports by residents | None shown | Unclear | LSOA | Uneven by council | S, V | held (new) |
| 15 | Public register of licensed premises | Gambling Commission | Betting shops, bingo halls, arcades, casinos, with address | Place | Conflicting. See below | Unclear | Address | Relies on councils reporting | S, V | held (new) |
| 16 | Alcohol licensing, England and Wales, to March 2024 | Home Office | Premises licences, 24-hour licences, cumulative impact areas | Place, by whole borough | OGL v3 | Yes | Licensing authority | Borough only. Five authorities estimated | S | held (new): too coarse |
| 17 | London's Night Time Economy by Borough and MSOA | GLA, from ONS data | Workplaces and employees in sectors that run in the evening or at night | Place | OGL v3 | Yes, with conditions | MSOA | Yes | S | held (new): data ends 2017 |
| 18 | Floorspace of night time economy establishments by town centre | GLA | Floorspace by town centre | Place | OGL v3 | Yes, with conditions | Town centre | Yes | S | none: data is for 2016 |
| 19 | UK Business Counts | ONS, on Nomis | Local business units by industry | Place | OGL, by the Nomis copyright page | Yes | MSOA | Yes | S | held (new) |
| 20 | Business Register and Employment Survey, open access | ONS, on Nomis | Jobs by industry | Place | OGL, with "further confidentiality restrictions" | Unclear | LSOA | Yes | S | held (new) |
| 21 | High Streets Data Service, members' data | GLA with boroughs and Business Improvement Districts | Spend, footfall, vacancy | Place | None found. Members only | Unclear | High street | Members only | S | held (new) |
| 22 | OS OpenMap - Local | Ordnance Survey | Street-level map layers | Place | OGL | Yes | Polygon and line | Yes | S | held (new) |
| 23 | MPS Recorded Crime: Geographic Breakdown | Metropolitan Police, hosted by the GLA | Recorded crime by LSOA | Events in a place | OGL v2 | Yes, with conditions | LSOA | Excludes City of London and transport police | R | held, as now |
| 24 | Single-borough files found on data.gov.uk: Camden's street cleansing schedule, premises licences for Hounslow and Ealing, industrial locations for Sutton and Kingston | Each borough | Varies | Place | OGL, as listed | Yes | Varies | One borough each | S | none: not London-wide |

Four of these need a word more.

**FixMyStreet (14).** mySociety published a statement on 6 February 2024. As read, asked word for word: "data from FixMyStreet cannot be used to definitively compare different areas in a fair manner", and "mySociety and SocietyWorks will not endorse the simplistic use of FixMyStreet data to compare, denounce or rank areas". It gives six reasons. Councils differ in whether they take reports this way. Categories are set by each council. And "people in areas of middle deprivation report the most problems via FixMyStreet, but that does not mean those areas have the most problems". Ranking areas is what Burro does. A licence would not cure this.

**Gambling Commission (15).** The Commission's terms of use say: "Copying any of this material is not permitted without prior approval from the owner of the relevant intellectual property rights." The data.gov.uk record for the same register, last updated 13 January 2022, says "UK Open Government Licence (OGL)". The register page states no licence and says the Commission "cannot provide any assurances on the completeness and accuracy of this data". The pages disagree, so the source is held until the Commission answers in writing.

**Land use (6).** The release groups Industry, Offices, Retail, and Storage and warehousing together as "Industry and commerce". The group total is therefore not a measure of industry. A feature must be built from the categories. The release says the figures come from Ordnance Survey's AddressBase, Open Greenspace and MasterMap Topography, and that the department is "considering the best timing and frequency for future editions". No edition later than 2022 was on the collection page.

**Fire incidents (7).** The metadata sheet lists 39 fields. Exact coordinates, postcode and UPRN are "redacted for Dwellings". Rounded coordinates are "rounded up to nearest 50". The sheet names the fields `IncidentGroup`, `StopCodeDescription`, `PropertyCategory` and `PropertyType` but not their values. The sample row's `PropertyType` is a place of worship, so that field can say what a building is used for. Whether outdoor rubbish fires can be picked out is from memory and unverified.

## What can be had at neighbourhood scale

An LSOA holds about 1,800 people, so a neighbourhood holds roughly ten. An MSOA holds about 8,000, so a neighbourhood holds two or three. A borough holds about fourteen neighbourhoods.

| The founder named | Finest open unit found | Good enough for 450 neighbourhoods? | Source |
|---|---|---|---|
| Recorded crime by type | LSOA | Yes | 1, 2 |
| Anti-social behaviour | LSOA | Yes | 1, 2 |
| Fly-tipping | Borough | No | 12 |
| Street cleansing, litter | England | No | 13 |
| Street problems reported by residents | LSOA | No. The publisher says not to rank with it | 14 |
| Vacant shops | None open | No | 21 |
| Betting shops | Address, if cleared | Not until the Commission answers | 15 |
| Takeaways | Point | Yes | 4 |
| Industrial land | LSOA | Yes, once the table is opened | 6 |
| Traffic | Count point, or road class | Road class yes. Flow only near count points | 5, 9 |
| Noise | LSOA, or grid | Yes. Transport noise only | 2, 10 |
| Graffiti and street art | None found | No | |
| Late licences | Borough | No | 16 |
| Rubbish fires | 50 m | Probably. Field values unverified | 7 |

## The Indices of Deprivation 2025: which parts describe a place

The Indices combine 55 indicators into seven domains and one overall index. The publisher's FAQ says two things that bear on "gritty" and "polished". "Within every area there will be individuals who are deprived and individuals who are not. The Index is not a suitable tool for targeting individuals." And: "The IoD25 is designed to identify aspects of deprivation, not affluence." So the low end of deprivation is not a measure of polish.

### By domain

Weights are from the statistical release. Indicator names are from the technical report, chapter 4 and appendix A.

| Domain | Weight | What is in it | Describes | In File 8 | May enter a tag under ADR 0006 |
|---|---|---|---|---|---|
| Income | 22.5% | People in households on means-tested benefits, and asylum seekers receiving support | Residents | One count per LSOA | No |
| Employment | 22.5% | Working-age people on out-of-work benefits, carers and incapacity benefits included | Residents | One count per LSOA | No |
| Education, skills and training | 13.5% | School attainment and absence, entry to higher education, adults with low qualifications or who "cannot speak English or cannot speak English 'well'" | Residents | Two of six indicators | No |
| Health and disability | 13.5% | Early death, disability benefits, emergency admissions, mental health | Residents | All four | No |
| Crime | 9.3% | Eight recorded rates. See below | Events in a place | All eight | Under the crime rules, not rule 8. See the decisions |
| Barriers to housing and services | 9.3% | Travel time, housing affordability, overcrowding, homelessness, broadband speed, patients per GP | Mixed | All | Indicator by indicator |
| Living environment | 9.3% | Housing condition, energy performance, outdoor space, air quality, road casualties, noise | Mixed | All | Indicator by indicator |

The task described crime, barriers and living environment as the domains that describe a place. That holds for crime. The other two are mixed, and the mix is inside the domain score.

### The three domains, by indicator

| Domain and sub-domain | Indicator as File 8 names it | Period | Describes | Note |
|---|---|---|---|---|
| Crime | Violence with injury, rate per 1,000 at-risk population | 2018/19 to 2023/24 | Events in a place | Includes homicide |
| Crime | Violence without injury | same | Events in a place | |
| Crime | Stalking and harassment | same | Events in a place | |
| Crime | Burglary, rate per 1,000 at-risk properties | same | Events in a place | Homes and business premises |
| Crime | Theft | same | Events in a place | Includes robbery. Excludes shoplifting |
| Crime | Criminal damage | same | Events in a place | Includes arson. Graffiti cannot be told apart |
| Crime | Public order and possession of weapons | same | Events in a place | |
| Crime | Anti-social behaviour | 2022/23 to 2023/24 | Events in a place | Incidents reported to police: "personal", "environmental" and "nuisance" |
| Barriers, geographical | Connectivity Score | 2025 | Place | Travel time on foot, by bike and by public transport. Higher is better in the file |
| Barriers, wider | Housing affordability | 2018 to 2022 | Residents and prices | Modelled from incomes. The report lists Zoopla among its inputs |
| Barriers, wider | Household overcrowding, rooms and bedrooms | 2021 | Households | Census |
| Barriers, wider | Homelessness, and core homelessness | 2020 to 2024 | Residents | Local authority figures repeated on every LSOA |
| Barriers, wider | Digital connectivity (broadband speeds) | December 2024 | Place, partly | Speeds of active lines, so it also reflects what households buy |
| Barriers, wider | Patient-to-GP ratio | November 2024 | A service | Spread to LSOAs by where patients live |
| Living environment, indoors | Housing in poor condition | 2023 | Buildings and residents | A model. The report says its inputs include "tenure and occupant characteristics" and names Experian dwelling-level data |
| Living environment, indoors | Housing energy performance | 2012 to 2024 | Buildings | About 40% of homes had no certificate and were given an estimate |
| Living environment, indoors | Housing lacking private outdoor space | 2023 | Buildings and plots | A 0 to 100 shortfall score. Shared space counts for flats |
| Living environment, outdoors | Air quality | 2023 | Place | From the same Defra model as `air_no2` |
| Living environment, outdoors | Road traffic casualties, pedestrians and cyclists | 2019 to 2023 | Events in a place | Weighted by severity |
| Living environment, outdoors | Noise pollution | 2021 | Place | Road, rail and aircraft. "Other sources, such as industrial noise, were excluded" |

How the crime rates were made matters. The technical report says the research team used police records with "the full police geocodes, not the geographically anonymised data released into the public domain". Counts were divided by residents plus an estimate of people who work in the area. Shrinkage was applied. So these rates are better located than anything Burro can build from data.police.uk. They are also frozen: the last month in them is March 2024, and the previous edition was 2019.

### What the registry approves today

The entry `mhclg-iod-2025-underlying-indicators` approves File 8 only, for `scoring` and `display`. Its conditions:

| Condition in the entry | What it means for grit |
|---|---|
| "Only place-based indicators may enter the product, and each needs a feature allowlist entry. The v1 indicator is noise exposure" | Criminal damage, ASB, road casualties and outdoor space are covered by the licence. Each needs a catalogue row before use |
| Indicators "that describe residents (income, employment, health, education) and the IMD rank or decile must never be inputs to ranking or tags" | The socioeconomic part of the founder's "gritty" is barred by the entry itself |
| Patient-to-GP ratio and broadband are out of v1 scope | The founder's item 7. Not this report's subject |
| "Not comparable with the 2019 indices" | No "getting grittier" or "cleaning up" |
| Read the notes sheet at first ingest | Done for reading. See the registry findings below |

Files 1 to 7 and 9 are not registered. They hold the ranks, deciles and domain scores. None should be registered for product use.

### What the file holds, measured

I counted rows where the local authority code begins `E09`. There are 4,994, and every one has a value in every crime, living environment and barriers column.

| Indicator | Lowest | Quarter | Middle | Three quarters | Highest | Distinct values |
|---|---|---|---|---|---|---|
| Criminal damage, per 1,000 at risk a year | 0.5 | 3.2 | 4.5 | 5.9 | 23.9 | 136 |
| Anti-social behaviour, per 1,000 at risk a year | 0.9 | 10.3 | 16.3 | 24.6 | 148.8 | 600 |
| Noise pollution, share of residents at 55 dB or more | 0.001 | 0.343 | 0.512 | 0.719 | 1.0 | 953 |

Criminal damage is published to one decimal place, so many areas tie. The noise column is a share from 0 to 1, not a percentage.

Rank correlations across the 4,994 London LSOAs, place-based columns only:

| | Violence with injury | Criminal damage | ASB | Noise | No outdoor space | Air quality |
|---|---|---|---|---|---|---|
| Criminal damage | 0.81 | | | | | |
| Anti-social behaviour | 0.64 | 0.61 | | | | |
| Noise | 0.23 | 0.19 | 0.29 | | | |
| No outdoor space | 0.40 | 0.32 | 0.49 | 0.47 | | |
| Air quality | 0.29 | 0.21 | 0.42 | 0.39 | 0.75 | |
| Connectivity | 0.29 | 0.21 | 0.43 | 0.39 | 0.78 | 0.84 |

These are at LSOA level. Figures for neighbourhoods will differ. They still show three things. Criminal damage and violence move together. Noise is nearly independent of both. Air quality, travel time and lack of gardens form one cluster, which is closeness to the centre.

## What could be built

### Two things, not one

| | Street character scale | Street incidents |
|---|---|---|
| What it says | How hard-edged or how polished the built place is | What was recorded as happening on the street |
| Built from | Land use, main roads, noise, density, green cover, conservation areas | Criminal damage, anti-social behaviour, rubbish fires |
| Direction | Either. A person can ask for the gritty end or the polished end | Less only. A person can ask to avoid it |
| Default | No weight until asked | Off until asked, as crime is now |
| In a tag | Yes. It is the tag | No |
| Describes | Place | Events in a place |
| Rule it changes | None | None |

Together they cover crime and the nearest measurable thing to cleanliness. They leave out the socioeconomic part.

### Features

| Proposed `feature_id` | Label | From | How | Describes | Honest limits |
|---|---|---|---|---|---|
| `land_industrial` | Industrial, storage and waste land as a share of the area | 6 | Sum the categories Industry, Storage and warehousing, Landfill and waste disposal, Minerals and mining | Place | As at April 2022. LSOA vintage unknown. Offices and retail are left out on purpose. Table not yet opened |
| `road_major_exposure` | Share of the area within 50 m of an A road or motorway | 5 | Buffer the road links by class | Place | Road class is not traffic. A quiet A road counts the same as a busy one |
| `venue_takeaway_share` | Takeaways as a share of places to eat and drink | 4 | "Takeaway/sandwich shop" over takeaways, restaurants, cafes, pubs and bars | Place | Sandwich shops are in the same type. Likely to follow income, so it waits for the proxy audit. Not in the draft formula |
| `incident_criminal_damage` | Recorded criminal damage and arson | 2 or 1 | The File 8 rate, weighted by residents | Events in a place | Recorded, not actual. Six-year average to March 2024. It tracks violence at 0.81 |
| `incident_asb` | Recorded anti-social behaviour | 2 or 1 | As above | Events in a place | Depends on who calls the police. Two years only. Transport police have sent no ASB data to data.police.uk since April 2016 |
| `incident_refuse_fires` | Outdoor rubbish fires attended by the fire brigade | 7 | Count by rounded coordinate, per km² a year | Events in a place | Field values unverified. A fire is attended only if someone calls |
| `road_casualties` | Pedestrian and cyclist casualties | 2 | The File 8 rate | Events in a place | Follows footfall. Optional |

Already in the catalogue and reused: `noise_exposure`, `homes_density`, `green_cover`, `conservation_cover`, `venue_evening`.

Not proposed as features: the housing condition indicator (mixed with occupant data), overcrowding, affordability, homelessness, and recorded drug offences. Recorded drug offences mostly follow where police search. That last point is my judgement and was not checked against a source.

### The scale: polished to gritty

One score. High is gritty. Low is polished.

| Draft formula, in hundredths | |
|---|---|
| `street_character` | 0.30 `land_industrial` high + 0.20 `road_major_exposure` high + 0.15 `noise_exposure` high + 0.15 `homes_density` high + 0.10 `green_cover` low + 0.10 `conservation_cover` low |

- The weights are a first guess. Nothing was measured. The tag ships only if it passes the 40-neighbourhood sanity set, and that set must hold places that people who know London call gritty and places they call polished.
- It measures hard-edged, not run-down. An industrial estate where nobody lives would score highest. Weighting by where people live, as the release already does for other features, reduces that.
- The polished end overlaps three tags Burro already has: `leafy`, `quiet_residential` and `historic_character`. The gritty end is what is new.
- Tags have one direction in the engine today. Asking for the low end of a tag is new, and is for the team that owns `packages/core`.
- `conservation_cover` carries 10 hundredths, under the 60 the contract allows.

**Is "gritty" better as one end of a scale? Yes.** A single tag called "gritty" reads as a verdict on a place. A scale with two named ends reads as a position, and it serves both the person who seeks it and the person who avoids it with one control. The condition is point 1 of the summary: nothing on the scale may be a nuisance.

### With the resident-describing parts

This is what the founder described. It is set out so the choice is clear, not because it is recommended.

| Added input | Source | What it would add | What it would cost |
|---|---|---|---|
| Income and employment domain scores | File 5 or 7, not registered | The everyday sense of "gritty" as "poorer" | It ranks residents. The income domain counts asylum seekers on support. The employment domain counts people on incapacity and carer's benefits |
| Overall index rank or decile | File 1, not registered | One familiar number | 72% of its weight is the four resident domains. It includes English language ability and disability benefits |
| Living environment domain score | File 2, not registered | Looks place-based | 70% of it is the indoors sub-domain, which includes the housing condition model |

### Experience

| Idea | What it needs | Rule it touches |
|---|---|---|
| A slider with two named ends, resting in the middle with no weight | The scale, and a way to ask for the low end of a tag | None |
| A "Street" block on every area page: industrial land, main roads, noise, each with figure, source and date | The features above | None |
| Street incidents shown only when the person turns them on, by category, with the crime caveat sentence | `feature_crime` template, already built | None. It follows the crime rules |
| The prompt reader hears "gritty", "edgy", "raw", "industrial", "polished", "smart", "manicured", "well-kept" | Rules vocabulary | None |
| The prompt reader does not map "rough", "dodgy" or "sketchy" onto the scale | Rules vocabulary. The verifier already bans these words in sentences | None |
| Words about who lives somewhere ("posh", "working class") get the one neutral sentence of contract section 8.4 | Rules vocabulary | ADR 0006, as it stands |
| Tap the scale to see its formula and sources | Methods page | None |
| A missing figure says so | Already the rule | None |

### Order of work

| Step | What | Done when |
|---|---|---|
| 1 | The founder makes decisions 1 and 2 below | Written in an ADR |
| 2 | Open table P405. Write down the LSOA vintage, the units and the categories | The gate on source 6 passes or fails |
| 3 | Add catalogue rows for the File 8 indicators chosen | The allowlist names them |
| 4 | Write the proxy audit row for each new feature, before looking at any correlation with residents | The rows exist |
| 5 | Spike: work out `land_industrial` and `road_major_exposure` for London. Test the scale on 20 places called gritty and 20 called polished | The scale separates the two lists, or the formula changes |
| 6 | Open one fire incident file. Check the property fields | The gate on source 7 passes or fails |
| 7 | Put the question to the Gambling Commission | It has been put |

## What cannot be done honestly

| Claim | Why not |
|---|---|
| "This neighbourhood's streets are clean" or "dirty" | No open data below borough level. The national survey covers England as a whole and last ran for 2018 to 2019 |
| A neighbourhood fly-tipping figure | Defra publishes by local authority. A borough's figure is not a neighbourhood's |
| A ranking built on FixMyStreet reports | The publisher says the data cannot compare areas fairly, and explains that reports follow who reports |
| "Few empty shops" | Vacancy data is for members of the High Streets Data Service. The rating list is banned |
| "Open late" or "late licences nearby" | Licensing figures are per borough. No open source of opening hours was found. `venue_evening` counts venues, not hours |
| Graffiti as a fact, or street art as a draw | No data found. Recorded criminal damage includes graffiti, arson and broken windows and cannot be split |
| "Gritty" as a fact about a place | It is a judgement. Burro can publish a formula and say where a place sits on it |
| Low deprivation as "polished" or "affluent" | The publisher says the Indices identify deprivation, not affluence |
| A deprivation domain score as a place measure | Living environment and barriers both mix place with residents inside the score |
| Noise from venues, neighbours or industry | The noise indicator covers road, rail and aircraft only |
| "Getting grittier" or "on the up" | The 2025 Indices are not comparable with 2019, and the land use table has one usable year |
| Crime at a station from data.police.uk | The changelog lists "British Transport Police: Crime data not provided" for each month from March 2025 to July 2026 |
| Criminal damage as a measure of upkeep alone | It tracks violence with injury at 0.81 across London's LSOAs |

## What the founder must decide

Work should proceed on the recommendation unless the founder says otherwise. Decision 1 touches rule 8 and the crime rules, and is the founder's alone.

### 1. What may go into "gritty"

| Choice | What goes in | What it allows | What it risks | What must change |
|---|---|---|---|---|
| A. Place only | Land use, main roads, noise, density, green cover, conservation areas | A scale a person can seek at either end | It measures hard-edged, not run-down. It will still follow deprivation | Nothing |
| B. Place only, with street incidents beside it | A, plus criminal damage, ASB and rubbish fires as separate figures, off until asked | Covers crime and the nearest thing to cleanliness. Both the seeker and the avoider are served | Two controls where the founder asked for one word | Nothing. The new incident features follow the crime rules as written |
| C. Street incidents inside the tag | One number that includes crime | One word, one number | A person who asks for "gritty" asks Burro to rank up recorded crime. The tag would rank areas much as recorded violence does. It is a composite that includes crime, which PLAN section 15 says Burro will not publish | ADR 0006 (crime by category, never rolled up). Contract 3.1 and 3.2 (crime in no tag, and the test that says so). PLAN sections 9 and 15 |
| D. Deprivation inside the tag | C, plus income, employment or the overall index | The everyday sense of the word | It ranks residents. The inputs include English language ability, asylum support and disability benefits, which are or sit next to protected characteristics. ADR 0007 says there is no budget for the legal view this needs | Rule 8. ADR 0006. PLAN sections 9 and 15. The registry entry's conditions |
| E. Deprivation shown on the area page, never ranked | A decile as context | A familiar official figure | It still describes residents to a person choosing where to live. The publisher says the index is "not a suitable tool for targeting individuals" | PLAN section 15 in spirit. A new registry entry with `display` |

Recommendation: **B**. It gives the founder crime and a relatable scale without touching rule 8. Not C, D or E at launch.

What would change it: ADR 0006 already says. "Legal advice that a specific resident-based input is safe, paid for once the product earns money."

### 2. One scale or one tag, and what to call it

| Choice | What it allows | What it risks |
|---|---|---|
| A. One scale, two named ends: "Polished" and "Gritty" | One control for seekers and avoiders | "Polished" implies the rest is not. Tags need a second direction in the engine |
| B. One tag called "Gritty", high only | Fits the engine as built | It reads as a verdict. People who live there may read it as an insult |
| C. A neutral name for the scale, such as "Street character", with the founder's words as the ends | The name passes no judgement and the ends stay relatable | Slightly less direct |

Recommendation: C. The word "gritty" is read by the prompt reader and shown as an end of the scale. No sentence says a place "is gritty". The tag sentence stays in the form the contract already uses: where the place ranks, of how many.

### 3. Which source for street incidents

| | data.police.uk (source 1) | Indices of Deprivation File 8 (source 2) |
|---|---|---|
| Location | Snapped to anonymised points | Full police geocodes, summed to LSOA by the publisher |
| Period | Monthly | Six years to March 2024. ASB two years |
| Refresh | Monthly | Not until the next Indices. The last gap was six years |
| Denominator | Burro builds its own | Residents plus people who work there |
| Small numbers | Burro must smooth | Shrinkage already applied |
| Gaps | Some forces and months missing | None in London |

Recommendation: File 8 for criminal damage and ASB, with the period printed beside the figure. The character of a street changes slowly, and location matters more than recency. Leave the two existing crime features on data.police.uk until someone decides whether to move them too. The two sources use different denominators, so their figures must not be compared on the page.

### 4 to 9. Smaller decisions

| # | Decision | Recommendation |
|---|---|---|
| 4 | Register the land use table and the fire incident records? | Yes, as `gated`, with the checks named in the entries below |
| 5 | Write to the Gambling Commission about the premises register? | Yes, but it is low priority. A count of betting shops needs a proxy audit row even if cleared |
| 6 | Use takeaway share in the scale? | Not until the proxy audit has a row for it. Show it as a fact on the area page if wanted |
| 7 | Show a borough figure on an area page, labelled as the borough's? | No. It is the same for every neighbourhood in the borough and reads as a fact about the neighbourhood |
| 8 | Ask mySociety for FixMyStreet data? | No. The publisher has said what it thinks of ranking areas with it |
| 9 | Add "gritty" to the verifier's allowed text, or to its banned words? | Allowed as a label and an end of the scale only. Never in a sentence about a place |

### Questions and pages

| To | Ask | Unblocks |
|---|---|---|
| Gambling Commission, communications team | May the public register of premises be downloaded and counted by area in a commercial product? Under which licence? The data.gov.uk record says OGL and the terms of use say copying needs approval | Source 15 |
| MHCLG land use statistics team | Will there be an edition after 2022? Which LSOA vintage does table P405 use? | Source 6 |
| ONS, through Nomis | Do the "further confidentiality restrictions" on the Business Register and Employment Survey apply to the open access tables at LSOA level? | Source 20. Only if source 6 fails |

## What this research turned up about entries already in the registry

I may not edit the registry. These are for whoever owns each entry.

| Entry | Finding | How read |
|---|---|---|
| `mhclg-iod-2025-underlying-indicators` | File 8 has eight sheets: Notes, and one for each of the seven domains. The Crime sheet holds all eight rates. The entry's notes now say that File 8 was opened once for this research | F |
| same | The notes sheet was read. A third-party copyright line appears on two indicators only, acute morbidity and mental health: "Hospital Episode Statistics Copyright © 2023, re-used with the permission of NHS Digital. All rights reserved." Both describe residents and are barred anyway. No crime or living environment row carries a copyright line. The sheet still needs saving to `registry/evidence/` by someone who may write there | F |
| same | The entry lists the resident domains as income, employment, health and education. It should also name household overcrowding, housing affordability, homelessness and housing in poor condition, which sit in the other domains and describe households or residents | F, P |
| same | The noise column is a share from 0 to 1. The catalogue gives the unit as %. The pipeline must convert | F |
| same | The noise indicator counts residents exposed, not homes. The catalogue label for `noise_exposure` says "Share of homes". The label should say people | P |
| same | File 8 publishes the suppressed and rounded counts for the income and employment domains. Ingest must read the named columns only and never load those sheets | F |
| `police-uk-street-level-crime` | The changelog lists "Metropolitan Police Service: Crime data not provided" for May, June, July and August 2024, and shows a later refresh only for February and March 2024. If those months are still missing, a 24-month window has a hole. Check the archive before the first ingest | S |
| same | The changelog lists "British Transport Police: Crime data not provided" for each month from March 2025 to July 2026, and a known issue that transport police have sent no ASB data since April 2016. The entry says all three London forces "are all on the download form". Being on the form is not the same as having data | S |
| same | The API lists 14 categories besides "All crime". "Criminal damage and arson" and "Public order" are separate categories | S |
| `fsa-food-hygiene-ratings` | The business type list was read from the agency's own endpoint. It has 14 types, among them "Takeaway/sandwich shop", "Pub/bar/nightclub", "Restaurant/Cafe/Canteen" and "Mobile caterer" | S |
| `dft-road-traffic-counts` | The downloads page offers count point data to 2025. Whether the count point files split out heavy goods vehicles was not stated | S |
| `gla-town-centre-boundaries` | The dataset page does not say whether the London Plan's night-time economy class is an attribute of each town centre | S |
| `docs/research/vibes/green.md`, step 4 | The outdoor space column is named "Housing lacking private outdoor space deprivation score". All 4,994 London LSOAs have a value, from 0.114 to 99.977 | F |

## What was not read

| What | Standing | What I relied on instead |
|---|---|---|
| Web search | None was made | Known addresses, guessed addresses, and publishers' own search pages. Unknown sources will be missing |
| Keep Britain Tidy's survey pages | Not read | Nothing. No claim is made about its surveys or terms |
| London Datastore search | Not read | data.gov.uk search, and direct dataset addresses |
| Defra's noise mapping dataset page | Not read | The registry entry |
| Defra's fly-tipping release text | Not read | The collection page, which names the local authority dataset |
| Copernicus Urban Atlas | Not read | Nothing. Not proposed |
| Overture's category list | Not read, and the guide did not list categories | Nothing. Whether Overture has categories for betting shops, pawnbrokers or street art is unverified |
| ONS figures on vacant homes | Not read | Nothing. Not proposed |
| Land use table P405 | Not opened. 36.4 MB, and the source is not registered | The release text. LSOA vintage, units and exact categories are unknown |
| Fire incident data files | Not opened. The source is not registered | The metadata sheet. Field values are unknown |
| The Gambling Commission register file | Not opened | The register page and the terms of use |
| The Indices of Deprivation research report | Not read | The technical report, the FAQ and File 8 |
| The 33 boroughs' own open data sites | Not surveyed | One data.gov.uk search for each of cleansing, graffiti, licensing and noise complaints |
| Any legal source on steering | Not read | ADR 0006 and ADR 0007 |

## Unverified

- That fire incident records can pick out outdoor rubbish fires. From memory of the field values, not from the file.
- That OS OpenMap - Local holds railway track as a layer. From memory.
- The LSOA vintage of the land use table.
- That recorded drug offences follow police activity more than street conditions. My judgement.
- That London has about 1,000 MSOAs and an LSOA holds about 1,800 people. From memory, used only for scale.
- Whether the Metropolitan Police months missing in 2024 were filled in later.
- Whether transport police crimes are inside the File 8 crime rates. The technical report names "individual police forces" without listing them.
- All wording marked S or V. The reader can paraphrase.
- The draft formula. Every weight is a guess.

## Proposed registry entries

Not yet in the registry. Each entry was loaded with the registry's own `Source` model and passed every rule in `rules.py` on 2026-09-23, with no errors and no warnings. No id clashes with the registry or with the other reports in this folder.

None is proposed as `approved`. Where the licence is plain, the entry says so and says what else holds it back. `gated` entries are the two this report recommends building on.

```toml
# Proposed by docs/research/vibes/grit.md on 2026-09-23.

# For registry/sources/environment.toml

[[source]]
id = "mhclg-land-use-statistics-2022"
name = "Land use statistics: England 2022, live tables by LSOA and MSOA (table P405)"
publisher = "Department for Levelling Up, Housing and Communities, now the Ministry of Housing, Communities and Local Government"
url = "https://www.gov.uk/government/statistics/land-use-in-england-2022"
dimension = "environment"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "Contains public sector information licensed under the Open Government Licence v3.0."
attribution_verified = false
conditions = [
    "Land use only: industry, storage and warehousing, landfill and waste disposal, minerals and mining, transport other than roads, vacant land. It describes land, never who lives on it.",
    "The data is as at April 2022. Show the vintage wherever a figure appears.",
    "The release says the figures are derived from Ordnance Survey AddressBase, Open Greenspace and MasterMap Topography. Use the published table only. Never ask for or use the inputs.",
    "The publisher has not said when the next edition will come. Treat it as a dated snapshot.",
]
status = "gated"
status_reason = "The release page states OGL v3.0 (read through a reader that summarises on 2026-09-23). Gate: (1) open table P405 and write down the LSOA vintage, the units and the exact categories, none of which the release text states; (2) read the notes in the table for any Ordnance Survey term that limits reuse of the figures; (3) the founder decides whether a street character scale is wanted. The 36.4 MB table was not opened, because the source was not registered."
uses = ["scoring", "display"]
cadence = "Irregular. Editions for 2017 to 2022. The 2022 edition was published on 27 October 2022. No later edition was on the collection page on 2026-09-23."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.gov.uk/government/statistics/land-use-in-england-2022",
    "https://www.gov.uk/government/statistics/land-use-in-england-2022/land-use-statistics-england-2022",
    "https://www.gov.uk/government/collections/land-use-in-england",
]
notes = "The release names 28 categories in 13 groups. The group 'Industry and commerce' holds Industry, Offices, Retail, and Storage and warehousing, so the group total is not a measure of industry: offices and shops are in it. Build the feature from the categories, not the group. The release says 0.2% of England is vacant land, so that category will be near zero in most areas."

[[source]]
id = "mhclg-planning-data-brownfield-land"
name = "Brownfield land (Planning Data platform)"
publisher = "Ministry of Housing, Communities and Local Government, from local planning authorities"
url = "https://www.planning.data.gov.uk/dataset/brownfield-land"
dimension = "environment"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "© Crown copyright and database right 2026. Licensed under the Open Government Licence v3.0."
attribution_verified = false
conditions = [
    "It is a register of sites that planning authorities judge suitable for housing. It is not a list of derelict or empty land. Never describe it as one.",
    "Keep the provider of each record, so that a borough with no records reads as unknown and never as zero.",
]
status = "held"
status_reason = "The licence is plain: the dataset page says 'Licensed under the Open Government Licence v.3.0' (read through a reader that summarises on 2026-09-23). It is held on fitness. The page says 'The data may be incomplete and not yet cover all of England'. How many London boroughs supply it was not measured, and a gap would rank boroughs by what they sent in. Promotion needs a count of records by London borough."
uses = ["prototyping_only"]
cadence = "The platform collects daily. 37,736 records from 298 providers on 2026-09-23."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.planning.data.gov.uk/dataset/brownfield-land",
    "https://www.planning.data.gov.uk/about/",
]

[[source]]
id = "defra-fly-tipping-statistics"
name = "Fly-tipping statistics for England, local authority dataset"
publisher = "Department for Environment, Food and Rural Affairs"
url = "https://www.gov.uk/government/statistics/fly-tipping-in-england"
dimension = "environment"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "Contains public sector information licensed under the Open Government Licence v3.0."
attribution_verified = false
conditions = [
    "Published for whole local authorities. A borough figure must never be shown or scored as a figure for a neighbourhood.",
    "Counts are incidents that councils recorded and dealt with. They follow how a council records as well as how much is dumped.",
]
status = "held"
status_reason = "Too coarse. London has 33 local authorities and Burro ranks about 450 neighbourhoods, so every neighbourhood in a borough would get the same figure. The licence is confirmed on the GOV.UK page (read through a reader that summarises on 2026-09-23). It would be promoted only if Defra published below local authority level."
uses = ["validation_only"]
cadence = "Annual. The 2024 to 2025 edition was updated on 25 February 2026."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = ["https://www.gov.uk/government/statistics/fly-tipping-in-england"]

[[source]]
id = "mysociety-fixmystreet-geographic-counts"
name = "FixMyStreet Geographic Counts (reports by LSOA and local authority)"
publisher = "mySociety"
url = "https://data.mysociety.org/datasets/fms-geographic/"
dimension = "environment"
licence = "None-stated"
commercial_use = "unknown"
share_alike = false
attribution = "Not applicable. Not ingested."
attribution_verified = false
conditions = [
    "Do not use it to compare or rank areas. The publisher says it cannot be used that way fairly, and says why.",
    "Do not collect reports from the FixMyStreet site or its feeds in place of this file.",
]
status = "held"
status_reason = "Two reasons. First, the dataset page shows no licence. Second, the publisher's statement of 6 February 2024 says data from FixMyStreet 'cannot be used to definitively compare different areas in a fair manner' and that mySociety 'will not endorse the simplistic use of FixMyStreet data to compare, denounce or rank areas'. It gives six reasons, among them that councils differ in whether they take reports this way and that people in areas of middle deprivation report most. Ranking areas is what Burro does. A licence would not cure the second reason."
cadence = "Not stated on the page."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://data.mysociety.org/datasets/fms-geographic/",
    "https://www.mysociety.org/2024/02/06/statement-from-mysociety-regarding-misuse-of-fixmystreet-data/",
    "https://www.fixmystreet.com/about/privacy",
]
notes = "A count of reports measures who reports as much as what is on the street, so it also leans towards describing residents. The privacy page says a Research Data Release policy 'may be seen on request'. It was not requested."

[[source]]
id = "os-openmap-local"
name = "OS OpenMap - Local"
publisher = "Ordnance Survey"
url = "https://www.ordnancesurvey.co.uk/products/os-open-map-local"
dimension = "environment"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "Contains OS data © Crown copyright and database right 2026."
attribution_verified = false
conditions = [
    "Set the year in the attribution to the year of the release that was ingested.",
    "Save the licence file from inside the download to registry/evidence at first ingest.",
]
status = "held"
status_reason = "Not needed unless the land use table fails its gate. The OS open data page lists OS OpenMap - Local among the products 'available for unrestricted, free commercial and personal reuse under the Open Government Licence (OGL)' (read through a reader that summarises on 2026-09-23). The product page did not list its layers, so whether it holds railway track and building outlines as separate layers is from memory and unverified."
uses = ["prototyping_only"]
cadence = "Six-monthly, as the product page states."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.ordnancesurvey.co.uk/products/open-data",
    "https://www.ordnancesurvey.co.uk/products/os-open-map-local",
]

# For registry/sources/safety.toml

[[source]]
id = "lfb-incident-records"
name = "London Fire Brigade Incident Records"
publisher = "London Fire Brigade, hosted by the Greater London Authority"
url = "https://data.london.gov.uk/dataset/london-fire-brigade-incident-records"
dimension = "safety"
licence = "OGL-2.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/2/"
commercial_use = "yes_with_conditions"
share_alike = false
attribution = "Contains public sector information licensed under the Open Government Licence v2.0."
attribution_verified = false
conditions = [
    "London Datastore site terms: state explicitly that the Greater London Authority cannot warrant the quality or accuracy of the data, and do not imply GLA endorsement.",
    "Outdoor rubbish and refuse fires only. Never load a fire in a dwelling. The metadata says postcode, UPRN and coordinates are 'redacted for Dwellings', and Burro must not try to undo that.",
    "Publish area rates only. Never show or export an incident row.",
    "The field PropertyType names kinds of building, places of worship among them. Never use it to say who uses a building or who lives nearby.",
    "OGL does not cover personal data. Do not try to link an incident to a person or an address.",
    "A fire count is never rolled into a safety score, and no sentence built on it may call a place safe or unsafe.",
]
status = "gated"
status_reason = "The dataset page shows 'Open Government Licence v2' (read through a reader that summarises on 2026-09-23). Gate: (1) open one data file and confirm that PropertyCategory and PropertyType pick out outdoor rubbish fires, which the metadata sheet does not state; (2) confirm that rounded coordinates are present for those rows; (3) the founder decides whether street incidents are wanted. No data file was opened, because the source was not registered. The 12 kB metadata sheet was read in full."
uses = ["scoring", "display"]
cadence = "The page says quarterly in one place and monthly in another. The file for 2024 onwards ran to July 2026 on 2026-09-23."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://data.london.gov.uk/dataset/london-fire-brigade-incident-records",
    "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/2/",
    "https://data.london.gov.uk/about/terms-and-conditions/",
]
notes = "The metadata sheet lists 39 fields. Location fields: Easting_rounded and Northing_rounded ('rounded up to nearest 50'), Postcode_district, ward and borough codes, USRN, and exact coordinates that are redacted for dwellings. The London Datastore terms page was not re-opened today. It is cited from the registry entry for the Metropolitan Police file."

# For registry/sources/places.toml

[[source]]
id = "gambling-commission-premises-register"
name = "Gambling Commission public register of licensed premises"
publisher = "Gambling Commission"
url = "https://www.gamblingcommission.gov.uk/public-register/premises"
dimension = "places"
licence = "Bespoke-terms"
licence_url = "https://www.gamblingcommission.gov.uk/terms-of-use"
commercial_use = "unknown"
share_alike = false
attribution = "Not determined. No licence is confirmed."
attribution_verified = false
conditions = [
    "Do not download the register until the Commission confirms the terms in writing.",
    "If cleared: counts by area only. Never show an operator's name or a premises row.",
    "A count of betting shops describes a place, but where they open follows who lives nearby. It needs a row in the proxy audit before it feeds a tag.",
]
status = "held"
status_reason = "The two pages disagree. The Commission's terms of use say 'Copying any of this material is not permitted without prior approval from the owner of the relevant intellectual property rights'. The data.gov.uk record for 'Licensed gambling premises', last updated 13 January 2022, says 'UK Open Government Licence (OGL)' and links to the same register. The register page itself states no licence, and says the Commission 'cannot provide any assurances on the completeness and accuracy of this data'. A written reply from the Commission settles it. All read through a reader that summarises on 2026-09-23."
cadence = "The register page showed 'last updated' 23 September 2026."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.gamblingcommission.gov.uk/public-register/premises",
    "https://www.gamblingcommission.gov.uk/terms-of-use",
    "https://www.data.gov.uk/dataset/8dc9bef0-ad46-497b-9a74-30a6ce9d2f98/licensed-gambling-premises",
]

[[source]]
id = "home-office-alcohol-licensing-statistics"
name = "Alcohol licensing, England and Wales, April 2023 to March 2024"
publisher = "Home Office"
url = "https://www.gov.uk/government/statistics/alcohol-licensing-england-and-wales-april-2023-to-march-2024"
dimension = "places"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "Contains public sector information licensed under the Open Government Licence v3.0."
attribution_verified = false
conditions = [
    "Published for whole licensing authorities. A borough figure must never be shown or scored as a figure for a neighbourhood.",
]
status = "held"
status_reason = "Too coarse. The tables are by licensing authority, which in London is the borough. The release says figures are rounded to the nearest hundred and that five authorities were estimated. The collection page states OGL v3.0 (read through a reader that summarises on 2026-09-23). No open source of late licences by premises was found for all of London."
uses = ["validation_only"]
cadence = "About every two years. Editions for March 2022 and March 2024."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.gov.uk/government/collections/alcohol-and-late-night-refreshment-licensing-england-and-wales-statistics",
    "https://www.gov.uk/government/statistics/alcohol-licensing-england-and-wales-april-2023-to-march-2024",
]

[[source]]
id = "gla-night-time-economy-by-msoa"
name = "London's Night Time Economy by Borough and MSOA"
publisher = "Greater London Authority, from Office for National Statistics data"
url = "https://data.london.gov.uk/dataset/londons-night-time-economy-by-borough-and-msoa-2w1g8"
dimension = "places"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes_with_conditions"
share_alike = false
attribution = "Contains public sector information licensed under the Open Government Licence v3.0."
attribution_verified = false
conditions = [
    "London Datastore site terms: state explicitly that the Greater London Authority cannot warrant the quality or accuracy of the data, and do not imply GLA endorsement.",
    "It counts workplaces and employees, which describes where work is done, not who lives there.",
]
status = "held"
status_reason = "Stale. The page says the data covers 2001 to 2017. The dataset page shows Open Government Licence v3 (read through a reader that summarises on 2026-09-23). It would be promoted only if the GLA published a newer edition."
uses = ["validation_only"]
cadence = "None seen. Last data year 2017."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://data.london.gov.uk/dataset/londons-night-time-economy-by-borough-and-msoa-2w1g8",
    "https://data.london.gov.uk/night-time-observatory/vibrancy",
]

[[source]]
id = "ons-uk-business-counts"
name = "UK Business Counts: local units by industry (Nomis)"
publisher = "Office for National Statistics"
url = "https://www.nomisweb.co.uk/sources/ukbc"
dimension = "places"
licence = "OGL-3.0"
licence_url = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
commercial_use = "yes"
share_alike = false
attribution = "Source: Office for National Statistics"
attribution_verified = false
conditions = [
    "Nomis terms: do not use the data to attempt to obtain or derive information about an identified person, household or business.",
    "A business is counted where it is registered or reports, which can differ from where the work is done.",
]
status = "held"
status_reason = "A fallback for industrial character if the land use table fails its gate. The smallest area is the MSOA, of which London has about 1,000. The Nomis copyright page allows reuse under the OGL 'whether commercially or privately' and names no extra limit on this series (read through a reader that summarises on 2026-09-23). The MSOA vintage and the rounding were not read."
uses = ["prototyping_only"]
cadence = "Annual, at a reference date in March, as the source page states."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.nomisweb.co.uk/sources/ukbc",
    "https://www.nomisweb.co.uk/home/copyright.asp",
]

[[source]]
id = "ons-bres-open-access"
name = "Business Register and Employment Survey, open access (Nomis)"
publisher = "Office for National Statistics"
url = "https://www.nomisweb.co.uk/sources/bres"
dimension = "places"
licence = "OGL-3.0"
additional_licences = ["Bespoke-terms"]
licence_url = "https://www.nomisweb.co.uk/home/copyright.asp"
commercial_use = "unknown"
share_alike = false
attribution = "Source: Office for National Statistics"
attribution_verified = false
conditions = [
    "The Nomis copyright page says this survey's data 'are subject to further confidentiality restrictions'. Read them in full before any file is opened.",
]
status = "held"
status_reason = "The Nomis copyright page singles this survey out: its data 'are subject to further confidentiality restrictions', and figures marked confidential may not be passed on without permission. Whether the open access tables at LSOA level are free of that limit was not established. A written reply from ONS settles it. Read through a reader that summarises on 2026-09-23."
cadence = "Annual."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://www.nomisweb.co.uk/sources/bres",
    "https://www.nomisweb.co.uk/home/copyright.asp",
]

[[source]]
id = "gla-high-streets-data-service-partnership-data"
name = "High Streets Data Service: spend, footfall and vacancy data for members"
publisher = "Greater London Authority with member boroughs and Business Improvement Districts"
url = "https://data.london.gov.uk/high-street-data-service/"
dimension = "places"
licence = "Bespoke-terms"
commercial_use = "unknown"
share_alike = false
attribution = "Not applicable. Not ingested."
attribution_verified = false
conditions = [
    "Members only. Do not ask a member to pass the data on.",
]
status = "held"
status_reason = "Not open. The service page says spend, mobility and business premises data are for members, who are boroughs and Business Improvement Districts paying to join. Its open data page lists boundaries only, and no vacancy or footfall figures. No licence text was found. Read through a reader that summarises on 2026-09-23. Nothing short of the GLA publishing vacancy openly would change this."
cadence = "Not stated."
verified_how = "primary_source"
verified_on = 2026-09-23
evidence_urls = [
    "https://data.london.gov.uk/high-street-data-service/",
    "https://data.london.gov.uk/high-street-data-service/open-data",
]
```

## Sources read

| Page | Address |
|---|---|
| Indices of Deprivation 2025, release page | https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025 |
| Indices of Deprivation 2025, statistical release | https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025/english-indices-of-deprivation-2025-statistical-release |
| Indices of Deprivation 2025, FAQ | https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025/english-indices-of-deprivation-2025-frequently-asked-questions |
| Indices of Deprivation 2025, technical report | https://www.gov.uk/government/publications/english-indices-of-deprivation-2025-technical-report |
| data.police.uk, about, changelog and category list | https://data.police.uk/about/ and https://data.police.uk/changelog/ |
| Fly-tipping statistics | https://www.gov.uk/government/statistics/fly-tipping-in-england |
| Litter dashboard | https://www.gov.uk/government/publications/litter-and-littering-in-england-data-dashboard |
| Land use statistics 2022 | https://www.gov.uk/government/statistics/land-use-in-england-2022 |
| Alcohol licensing statistics | https://www.gov.uk/government/collections/alcohol-and-late-night-refreshment-licensing-england-and-wales-statistics |
| Brownfield land | https://www.planning.data.gov.uk/dataset/brownfield-land |
| London Fire Brigade incident records | https://data.london.gov.uk/dataset/london-fire-brigade-incident-records |
| High Streets Data Service | https://data.london.gov.uk/high-street-data-service/ |
| Night Time Observatory | https://data.london.gov.uk/night-time-observatory/vibrancy |
| mySociety statement on FixMyStreet data | https://www.mysociety.org/2024/02/06/statement-from-mysociety-regarding-misuse-of-fixmystreet-data/ |
| mySociety datasets | https://data.mysociety.org/datasets/ |
| FixMyStreet privacy page | https://www.fixmystreet.com/about/privacy |
| Gambling Commission register and terms | https://www.gamblingcommission.gov.uk/public-register/premises and https://www.gamblingcommission.gov.uk/terms-of-use |
| Food hygiene business types | https://ratings.food.gov.uk/open-data |
| Nomis copyright, business counts, employment survey | https://www.nomisweb.co.uk/home/copyright.asp |
| Road traffic downloads | https://roadtraffic.dft.gov.uk/downloads |
| OS open data | https://www.ordnancesurvey.co.uk/products/open-data |
