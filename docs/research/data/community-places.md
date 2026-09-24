# Places of worship and centres nearby: what is built, and what it waits on

Written 2026-09-24. A dated snapshot, not a source of truth.

**Since this page was written** the founder has stated the period of the file, the part has its receipt, and the measures have been worked out on it: [what the real file gave](culture-and-community-on-the-real-file.md). What follows is as it stood before. Where the two differ, the later page stands.

**No figure of a real place is on this page.** When it was written none had been worked out: the part of the file of places was in the store, and it had no receipt. A step reads a file through its receipt and in no other way, so no step has read it. Everything here was built and driven on a made-up file, laid out as the publisher's own pages say its file is. No person has checked anything here.

It follows the founder's decision of 24 September 2026: a person reaches a community through what is there, and never through a count of who lives somewhere. It builds on [culture nearby](culture-venues.md), and reads the same part of the same file by the same code.

Credit: Overture Maps Foundation, overturemaps.org. Records from Meta and Microsoft are under CDLA-Permissive-2.0, from Foursquare under Apache 2.0, and from AllThePlaces under CC0.

## 0. In short

| Question | Answer |
|---|---|
| What is it for | A person who types "near a mosque". Today the words are heard and answered with nothing |
| What is counted | Buildings within 800 metres of home, in a straight line: places of worship, and of them churches, mosques, synagogues, Hindu temples, gurdwaras and Buddhist temples. Community centres and cultural centres |
| From what | The part of one file of Overture Maps Places, release `2026-09-23.0`, that the list `m2-culture` takes. Registry id `overture-places`, approved for `scoring` |
| Is the part in the store | Yes: 42,484,081 bytes. It has no receipt, because the list is not sure of the period of the file |
| Has any real figure been worked out | No |
| How is the kind decided | By the most particular category of a record. Never by a name: no name is read |
| What is it never | An estimate of who lives somewhere. A score. An offer of fewer. A test holds each |
| Is it in a release | No. Core holds no feature for any of the nine figures |
| What does the reader do | [What the reader must do](../../design/community-reader.md), with thirty sentences |
| What is for the founder | Section 10 |

## 1. The file, and what it says of itself

| | |
|---|---|
| The list | `fetch/lists/m2-culture.toml`, one item: `overture-places-london` |
| What `describe` gives for the part in the store | 42,484,081 bytes, and that it looks like a Parquet file. Nothing else |
| What `describe` cannot give | It reads no footer of a Parquet file. So it says nothing of the rows, of the period, or of how the layout names the columns inside `sources` |
| What was put right in the list | `max_bytes` was a guess of 250 MB and was marked unsure. It is now 60,000,000, above the part as it was kept, and is no longer marked |
| What is still marked unsure | The period. The list states the day of the release. Whether that is when the places are as at is a person's to decide. A first look found that most records of one of the publisher's sources were last changed in 2019 or before |
| What writes the receipt | A person states the period in the list. `fetch --list m2-culture` is then run again: the same part is the same bytes, and its receipt is written |
| What runs then | `tests/derive/test_community_on_the_real_files.py`, which is skipped until the receipt is there. It holds the table of kinds to the file |

## 2. The publisher's categories

The publisher's own table of categories for the release was read through a reader that extracts the text of a page. An extraction is not the page. Each branch was asked for twice, in different words, and what both answers gave is kept. The table was read as far as its branch for health care. The branches after it were not read.

| Branch | Asked | Both answers gave | Kept |
|---|---|---|---|
| Places of worship, and what stands beside them | Twice | The same 73 rows | All 73 |
| Community and cultural centres | Twice | The two centres, and eight categories beside them. One answer gave 17 more rows of the same branches | The two as counted, and six as left out by name. The other two are parents, and are read as no centre |
| Places to eat, by cuisine | Twice | The same cuisines of a country. One answer gave the more particular rows under them | The cuisines of a country: section 7 |
| Shops that sell food | Twice | **Nothing.** One answer listed grocers by cuisine and by diet, in the words of the question. The other found no line that holds "grocery", "supermarket" or "butcher" | Nothing. The branch for shops stands after the last branch that was read. The first answer was made up from the question |

### 2.1 Places of worship: used

All stand under `cultural_and_historic > place_of_worship`.

| Kind | The head of its branch | Under it | Categories |
|---|---|---|---|
| Church | `christian_place_of_worship` | Church of the East. Eastern Orthodox, and seven under it. Oriental Orthodox, and six. Protestant, and eight. Restorationist, and two. Roman Catholic, and two | 32 |
| Mosque | `muslim_place_of_worship` | Ibadi, Shia, Sunni | 4 |
| Synagogue | `jewish_place_of_worship` | Conservative, Orthodox, Reconstructionist, Reform | 5 |
| Hindu temple | `hindu_place_of_worship` | Shaiva, Shakta, Smarta, Vaishnava | 5 |
| Gurdwara | `sikh_place_of_worship` | None | 1 |
| Buddhist temple | `buddhist_place_of_worship` | Mahayana, and three under it. Theravada. Vajrayana | 7 |
| Of no kind named | `place_of_worship` | | 1 |

A record under a kind is of that kind, however particular its own category. The denominations are read and are not told apart.

### 2.2 Places of worship: left out

| Branch, under `cultural_and_historic` | Categories | Why |
|---|---|---|
| `religious_landmark` | It, `pilgrimage_site` and four under that, `shrine` and three under that: a Catholic, a Shinto and a Sufi shrine | A landmark. The publisher files it apart from a place of worship |
| `religious_organization` | It, `convent`, `monastery`, `seminary` | An organisation or a house of an order |
| `religious_retreat_or_center` | It, `christian_retreat_center`, `hindu_ashram`, `zen_center` | A retreat |

### 2.3 What the tree does not hold

As far as it was read, the tree has no category of a place of worship for any belief but the six. A Jain temple, a Baha'i centre, a Zoroastrian temple and a Quaker meeting house have none. Where such a building is in the file, it is filed under `place_of_worship` alone, or under something else, and the table cannot tell which.

### 2.4 Centres

| Counted | The publisher's category | Left out beside it |
|---|---|---|
| Community centre | `community_and_government > social_or_community_service > community_center` | `civic_center`: a building of a council. `youth_organization`: a body, and no place |
| Cultural centre | `cultural_and_historic > cultural_center` | `social_club`, `country_club`, `fraternal_organization`, `veterans_organization`: a club for its members |

One answer alone gave a category of its own for a scout hall. A first look found that half the records under a community hall were scout groups from one feed. Whether this release files them apart is not known until the file is read.

## 3. The measures

Nine figures for every area. Each is the number of buildings within 800 metres of home, in a straight line, as the mean over the area's homes.

| Figure | Its id | Module |
|---|---|---|
| Places of worship | `worship_places` | `derive/worship_nearby.py` |
| Churches, mosques, synagogues, Hindu temples, gurdwaras, Buddhist temples | `worship_churches`, `worship_mosques`, `worship_synagogues`, `worship_hindu_temples`, `worship_gurdwaras`, `worship_buddhist_temples` | `derive/worship_nearby.py` |
| Community centres | `community_centres` | `derive/centres_nearby.py` |
| Cultural centres | `cultural_centres` | `derive/centres_nearby.py` |

- **The same reach and the same code as cultural venues.** Where homes are, how far a building may be, the mean over homes and the edge of London are `derive/culture_reach.py`'s. What the two measures share is `derive/places_counted.py`. The file is read by `culture_file.records`, which reads the columns that culture reads and no other.
- **A record of no kind named** counts toward places of worship and toward none of the six. Where it stands within 25 metres of a building of a kind, it is that building again and adds nothing.
- **One building with many records counts once, where they stand together.** Records of one kind within 25 metres of the first of them are one building, and the first is the most westerly. On the made-up file, five records of one church on one spot are one building, and so are five that stand within 12 metres of its middle. Five that each stand within 20 metres of its middle are four buildings, because those at its ends stand 40 metres apart. How often the real file does that is not known. `close_together` counts the buildings of each kind that stand within 50 metres of another of the same kind, so that a person can look. It changes no figure.
- **One building that is filed under two kinds** counts once under each, and so twice among places of worship.
- **What a record says beside its category decides nothing.** A community centre that also gives a category of a mosque is a community centre. Such records are counted by kind, so that a person can see how many the rule passes by.
- **Nought** is a count only where the file holds a record of any kind within the same reach, as for cultural venues.
- **A cultural centre is of no named culture.** The category does not say whose a centre is. A name would, and no name is read.
- **The two centres are not added up**, and there is no figure of both, in the rows or behind them.
- **What a measure hands back holds no count of homes**, and cannot be asked how many kinds are within reach. The code of cultural venues holds both. Neither is handed on.

## 4. What the measures never do

| Never | How it is held |
|---|---|
| An estimate of who lives somewhere | Every figure is a count of buildings. None is a share, a rate or a figure for each so many homes. No module of the measure divides anything. No file about who lives anywhere is opened. How many homes stand somewhere changes no count of what is within reach of one of them. No word that is shown says who lives or who goes anywhere. What a measure hands back holds no count of homes, so no count can be set over one. `test_a_count_of_buildings_is_never_turned_into_an_estimate_of_who_lives_there`, `test_what_is_handed_back_cannot_be_made_into_a_rate_or_a_count_of_kinds` |
| A score of how much of a community an area has | One figure for each kind, and the plain number of places of worship. No kind is weighed against another. No figure says how many kinds are within reach. Every row is put forward as weighed on request only, which core lets into no vibe. `test_the_counts_are_never_added_up_into_a_score_of_how_much_of_anything_an_area_has` |
| A direction of fewer | More is the one direction of every row. Every offer ends "nearby". `test_a_count_is_never_offered_with_a_direction_of_fewer` |

## 5. Does it say something

It has not been asked of a real file. `held_against_the_centre` in `derive/places_counted.py` holds each figure against homes per hectare, against how far an area's homes are from the middle of London's homes, and against a count of every record within the same reach, by rank correlation. It is built and tested, and the test on the real file is written.

What is expected, and is not known:

| Expected | Why |
|---|---|
| Places of worship and churches follow the centre | A first look found that a count of one kind of place stands in almost the order of a count of everything |
| The five other kinds do not | There are few of each, and they stand where they were built. Most areas will read nought |
| The count of a kind is nought in most areas | So it puts few areas in order. It answers "is one near" more than "how many" |

## 6. By borough, and whether the map is believable

Not known. No count by borough has been made. When the receipt is there, these are what to look at first, in a folder that git ignores:

| # | What | What would look wrong |
|---|---|---|
| 1 | The records of each kind in the part, and the buildings they are | A kind with none: a fault of the table. A kind with under 20 in all of London |
| 2 | The records of no kind named, against those of a kind | More of no kind than of all six: the counts of the kinds are then short |
| 3 | The records that name a place of worship beside another category | Many of one kind: buildings of that kind are filed as halls, and the count misses them |
| 4 | The buildings of each kind by borough | A borough with no church. A borough known for a kind of building with none of it |
| 5 | The records of each kind by the publisher's source | A kind that one source alone gives |
| 6 | The three correlations of each figure | 0.9 or more with the count of every record |
| 7 | The buildings of each kind that stand within 50 metres of another of the same kind | More than a few in 100 of a kind: one building is being counted more than once, and 25 metres is too short for this file |

**What the file is likely to miss.** It is gathered from what organisations and others have put on the web. A building with a page of its own is likely to be in it. A group that meets in a hired hall, a school, a shop front or a house is not, because the file lists such a place as what it is filed as. How that falls across the kinds is not known, and it is unlikely to fall evenly. So a low count of one kind is never proof that few such buildings are there.

**A register to hold it to.** One was read and is not registered: section 9.

## 7. Cuisines: variety alone

The design of the vibes wants how many cuisines are within reach, as 20 in 100 of Food and drink. It was worked out in a folder that git ignores, on a made-up file, by the code above and the slots of `culture_reach.py`. It is not a module, and nothing of it is committed.

| | |
|---|---|
| What a cuisine is | A category of the publisher's tree that names the cooking of a country: 109 of them, which both readings gave. A record under one is of that cuisine, however particular its own category |
| What is no cuisine | A parent of cuisines alone, such as `asian_restaurant`. A dish or a way of serving, such as `burger_restaurant` and `buffet_restaurant`. A diet, such as `vegan_restaurant` |
| What is left out on purpose | `halal_restaurant`, `kosher_restaurant` and `jewish_restaurant`. The publisher files each as a diet. Each is left out of the count of variety, so that the count never stands in for who lives somewhere |
| The figure | How many cuisines have a place to eat within 800 metres, as the mean over the area's homes |
| What is not built | A figure of any one cuisine |
| Shops | Not known. The branch of the table for shops could not be read |

## 8. Schools with a religious character

Nothing is built on it, and the column is not read. The founder decided on 24 September 2026 that the religious character of a school is not counted as an amenity, and that schools are counted without regard to faith. The registry's condition on the column still says "until the founder decides". It is for whoever applies the decisions to make it a standing rule.

## 9. A register of places of worship, read and not registered

| | |
|---|---|
| What | Places of worship registered for marriage |
| Publisher | HM Passport Office, on GOV.UK |
| Page | `https://www.gov.uk/government/publications/places-of-worship-registered-for-marriage` |
| File | One spreadsheet, of 1.94 MB as the page gives it. Its address was read twice and is not written here, because the source is not registered |
| Last updated | 9 September 2026, as the page gives it |
| Licence, as read | "All content is available under the Open Government Licence v3.0, except where otherwise stated". It is the line at the foot of the page, and says nothing of the file |
| What it leaves out | "This list does not cover Church of England/Church in Wales premises (Anglican premises)." A building that was never registered for marriages is not in it |
| What it could do | Hold the count of each kind in the file of places against a register, borough by borough, for every kind but Anglican churches. It can show what the file of places is missing. It cannot show what is there |
| What it must never do | Feed a figure. It would be registered for `validation_only` |
| Why it is not registered | The licence line is of the page and not of the file, and nobody has opened the file. A source whose licence is not clear is the founder's to add |

## 10. What is needed

| # | What | Whose |
|---|---|---|
| 1 | State the period of the file of places in the list, and fetch again for the receipt | The founder's |
| 2 | The test on the real file, and section 6 | Follows 1 |
| 3 | The nine features in core, and the reader: [the design](../../design/community-reader.md) | Core's |
| 4 | Whether a place of worship is offered, or applied when asked for plainly | The founder's |
| 5 | Whether an area is put in order by how many buildings of a kind are within reach, or by whether one is | The founder's |
| 6 | Whether the counts are shown on every area's page, or only the kinds a person asked for | The founder's |
| 7 | Whether a share keeps the kind of place of worship a person weighed | The founder's |
| 8 | Whether places to eat that are filed as halal or kosher are counted on request | The founder's |
| 9 | Whether a shrine, a monastery, an ashram and a Zen centre are places of worship | The founder's |
| 10 | Whether 25 metres is the right distance for records to be one building. Whether one is within reach does not change with it. How many are does | The founder's, once section 6, row 7, is known |
| 11 | Whether the register of section 9 is registered, for checking only | The founder's |
| 12 | A sample of records of each kind looked at by a person | The founder's |
| 13 | The branch of the publisher's table for shops, read by a person | The founder's |
| 14 | Whether `describe` should print what the footer of a Parquet file says: its rows and the names of its columns | The pipeline's |

## 11. What was not done

- No real file of places was read, so no count, no figure and no correlation of London is known.
- No count by borough was made.
- The table of kinds was not held to a file, and was read through a reader that extracts.
- The measures were not added to the measures of a build, and no release carries them.
- Core, the API and the website were not changed.
- No source was added to the registry, and no use of one was changed.
