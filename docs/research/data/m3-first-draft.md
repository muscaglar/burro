# The first whole draft of London's areas

Status: made on 2026-09-24, from the files in the store that day. Two checkers read it the same day, and it was made again after what they found. It is a dated snapshot of a draft: what a method made and no person has checked. No person has read a name or looked at a border at the review desk. Every number of every rule is a first guess.

It is written for the founder, who decides at the review desk, and for whoever makes the next draft. It holds counts, and the ids Burro gives its own areas. It holds no row of any file and no name of a place: a borough is named here by its place in the order of `made/flags/order.csv`. The credit of each publisher is at the foot. The draft itself is made from publishers' files, so it is in no tracked folder. [The areas design](../../design/london-data-areas.md) is what was built, and its sections 16 to 18 say what was decided where it was open. [What the files hold](m3-files.md) describes the files.

## 1. In short

| Question | Answer |
|---|---|
| Is every home in one area | Yes. 26,369 output areas, each in exactly one of 488 areas. None lies on both banks of the tidal water. By the generalised outlines none is in two pieces. By the full outlines one is: section 6 |
| Does every area have a name | 487 of 488. One has none. Its item at the desk shows the name it was grown from and the two names nearest to it, each with its record and how far off it lies |
| Where do the names come from | Ordnance Survey and the Greater London Authority, as each writes them. None from a person, a model or OpenStreetMap |
| How many names rest on two publishers | 154 of 487, and 134 of them letter for letter. One publisher writes the other 333. The design asks for two, and leaves the rule to the founder |
| Does it rest on a file with no receipt | Yes: the town centres. 355 areas rest on it, and each says so in its own row and on its own item |
| Can a name be turned down | Not at the desk, which cannot take the ground from under an area. The draft is made again from the desk's answers: section 9. So names are read before any border |
| Does a doubt of the draft reach the person who decides | Yes. Every mark and every flag is a line of the item it is about: 2,691 lines of names and 5,835 of borders |
| How long does it take to make | 85 seconds for the draft, and 4 seconds to fill the queues and lay the lines over them |
| Does it repeat | Yes. Two runs gave the same bytes in all 575 files |
| How many hours of decisions | 48.7 at the design's pace, as before. No item was taken out: no rule of the design says that one is noise. Eight rules put to the founder would take out 10.7 hours, were all adopted: section 7 |
| Did the borders change | No. Every output area is where the first draft put it. Five other names lie in another area than before, because a point on a line is now said to lie on it |

## 2. How it was made

One command makes all of it: `python -m burro_pipeline.areas.draft_run --out FOLDER`. It reaches no network, writes nothing to the store, and asks the licence gate for `gazetteer` before every file.

| Step | What happens | Each number chosen |
|---|---|---|
| Candidates | Every record that names a place: populated places of OS Open Names, town centres, wards and boroughs of Boundary-Line | Records of one name within 1,000 m are one place. A town centre wholly in the box of a place of its name is that place |
| Points | Each place is weighed by section 6 of the design | 3 for a populated place. 2 where 50 road records name it. 3 for a town centre of district class or above within 800 m. 1 for a ward that carries its name |
| Seeds | A name with enough points is put forward as an area. Its seed stands on its own town centre, or on its own point | 4 points, from one publisher or two. The design's 6 from two gives 363. Of two seeds within 600 m by road, the lighter gives way. A city in a box over 1,750 hectares is a wide name |
| Decisions | What a person said of a name at the desk is laid over the seeds, once the points asked for are chosen | None has been given. With `--decided`, a name that was turned down is no seed |
| Ground | Output areas, their centres, the roads, the wards, and the tidal water as Boundary-Line leaves it out of the land | Roads are read 2,000 m beyond London. Water under 100 hectares is left out. A seed starts from a piece of the roads of 50 nodes or more |
| Grow | Each output area goes to the seed with the least weighed distance along the roads, of its 3 nearest, on its own bank | A distance is cut by 15% where the roads name the seed's place and 5% where the ward does. It is raised by 10% across a borough line. No cut for an MSOA name: the gate refuses the source |
| Repair | A part cut off joins the area it shares most border with. An area too small joins its neighbour | The least size is 12 output areas. It is a guess of its own and rests on no table: the gate does not give homes |
| Name | Each area is offered the name it was grown from, where a record of that name lies in it | A point lies in the area of its output area, and on a line in every area it touches. An outline lies in an area that holds a twentieth of it or more |
| Flag | Twelve rules say what to look at, and the areas are put in order by what is at stake | Seeds within 600 m. Under 25% of a border along a borough line, a ward line or a main road within 20 m. Over 3 times the neighbours' size. A fifth of an area at a margin under 10%. The least compact 5%. Two town centres |
| Lines | Every mark and every flag is said in words, by the item of the desk it is about | Every output area in doubt is a line, with up to 4 streets that run in it, from OS Open Roads with local roads kept |
| Rules | What each of eight rules would settle is counted and listed. None is applied | Section 7 |
| Layers | What a reviewer sees behind a border, for each borough and 500 m round it | Wards and roads are thinned by 5 m, town centres by 2 m. Local roads are left out of the layer |
| Pictures | London, and each borough, drawn from the outlines and the layers. No basemap | Two areas within 400 m of each other are given two colours |

## 3. What was counted

| What | Count | Note |
|---|---|---|
| Output areas | 26,369 | Each in one area |
| Candidate records | 1,661 | 1,427 of Ordnance Survey, 234 of the Greater London Authority |
| Places | 781 | 690 known by a populated place, 91 by a town centre alone |
| Seeds | 516 | Put forward as areas |
| Areas | 488 | 28 seeds stand for no area: 26 held under 12 output areas, 2 were given none |
| Areas named for the name they were grown from | 484 | |
| Areas named for another name that lies in them | 3 | The name they were grown from lies outside. Marked `not_its_seed` |
| Areas with no name | 1 | `lon-n0538`. Its seed lies 290 m outside it |
| Areas whose name a point places | 463 | 4 more than first counted: their own point stands on their own edge. The other 24 are placed by an outline alone |
| Areas whose name two publishers write | 154 | 134 letter for letter. For 20 the second publisher writes the name beside another name, or with its own word for a centre after it, or with other marks |
| Other names | 301 | 289 smaller places inside, 4 other names of the same ground, 8 rows of 2 wide names |
| Rows of evidence | 1,266 | 320 are of a ward. The desk is handed the other 946 |
| Relations | 106 | 94 `name_lies_over`, 8 `same_name`, 4 `grown_from_a_name_in` |
| Marks to settle | 391 | On 245 names. 345 are grave. One says that a name may say who lives there |
| Areas in two boroughs or more | 169 | 1,674 output areas lie outside the main borough of their area. For one area, `lon-n0614`, the main borough is a tie |
| Areas with a flag about the border | 279 | 177 with one, 82 with two, 20 with three or more |
| Areas flagged at the desk | 230 | By the four flags the desk has words for. 49 more are flagged by the draft alone |
| Output areas in doubt | 4,955 | 3,341 at a margin under 10%. Every one is a line of its border |
| Lines for the desk | 8,526 | 2,691 of names, 5,835 of borders |
| Files read | 8 | 7 with a receipt, 1 with none |
| Layers | 251 files | 232 that the desk draws, 19 of tidal water that it has no layer for |
| Pictures | 34 | London and 33 boroughs |

| Size of an area | Least | Median | Most |
|---|---|---|---|
| Output areas | 12 | 49 | 208 |
| Hectares | 21.5 | 231.9 | 2,239.2 |

50 areas hold under half the median of output areas, and 33 hold over twice. A tenth hold 24 or fewer and a tenth hold 86 or more.

## 4. Against the design's guesses

| | The design guessed | The draft | What follows |
|---|---|---|---|
| Names to read | 1,100 | 789: 488 areas and 301 other names | 9.8 hours at the desk, against 14. Wikidata would add names: it has no file |
| Areas | About 450, of 400 to 500 | 488 | In range. By the design's own rule of 6 points from two publishers it is 351, under range |
| Flagged areas | About 120 | 279 by every rule. 230 by the four rules the desk has words for | 31 hours against 16. The first 120 of the order hold 56% of what is at stake |
| Areas resting on two publishers | All | 154 of 487 | The founder decides whether one official publisher is enough. It is one decision, not 333 |
| Other names | 300 to 500 | 301 | |
| Wide names | About 30 | 2 | The design expected them from Wikidata |
| Rows of evidence | 1,500 to 3,000 | 1,266 | |
| Relations | Under 200 | 106 | At a twentieth of an outline it would be 502, so a relation asks for a third |
| Time to build | Under 15 minutes | 85 seconds | |

The second draft, by the design's own rule, is beside the first. It has 351 areas of up to 336 output areas, none unnamed, 436 other names and 237 areas flagged about the border. It does not take out the names that look like a street or a building: all seven of those are areas in both drafts.

## 5. What the checks found, and what was done

Two checkers read the draft and the queues. One held the draft to the design's promises. One sat at the desk. They wrote 31 findings. Nothing was found that came from memory, from OpenStreetMap or from a table about who lives anywhere.

| Found | Done |
|---|---|
| An area could not be turned into another name or dropped. The desk set the answer aside, and the draft could not be made again without the name | A run reads the desk's answers with `--decided`, and the kept list with `--kept`. Driven with the desk's own `compile`: seven answers set aside by the desk gave a draft of 481 areas, with 290 output areas gone to 24 neighbours and every other id as it was |
| One seed's dot bore the name of its area, at a point where no record puts that name | A seed is drawn under the name its own record writes. 685 dots, none under another name |
| The one name that may say who lives there was flagged nowhere the founder looks | It is flagged `describes_residents` at the desk, is the first row of `names_to_look_at.csv`, and is the first line of its item |
| The draft's marks did not reach the item: 1,939 rows in a file the founder is not told to read | Every grave mark is in `names_to_look_at.csv` with its item, and is a line of the item. `about.txt` says where each is written |
| A ward's label could be picked as the name of an area, on 316 items | The desk is handed no row of a ward. 0 items offer one. The ward is still said, as a line |
| A border item did not say what its flag found | Every flag's sentence is a line. It names the boroughs, the town centres, the counts |
| A cell was known by its code alone, and cells in doubt beyond six were not listed | Every output area in doubt is a line, which the desk rings, with the streets that run in it. 4,898 of 4,955 have a named street |
| 49 areas the draft flags were not flagged at the desk | They are said in a line, and come after the flagged areas of their borough and before the rest. They carry no flag at the desk until it has words for seven flags: section 10 |
| Over half the names show nothing a person can weigh. 39 borders are flagged for one to four cells | Eight rules are put to the founder, each with what it would settle. None is adopted: section 7 |
| The points rule lets a name in for standing near a town centre of another name | The item says which centre gave the points, and whether it is of another name. 95 of 516 names put forward reach their points only so. The founder decides: section 7 |
| Seven areas are named for what looks like a street or a development | Left as they are: turning a name down is a person's decision. They are 7 of the 19 names the sixth rule would settle. Names are read before borders, so no border is reviewed twice |
| The ten largest areas cannot be made smaller at the desk | Listed in `largest_areas.csv`, by output areas. In 6 of them no other name lies. A person can make an area of another name by hand, in the file of decisions |
| 17 names were placed by the order of codes, where a point lies on a line | A point on a line lies in every area it touches. 4 areas are no longer told that no point of their name lies in them. 17 names are marked `on_the_line` |
| 154 names on two publishers is 134 letter for letter | Both are counted. `name_evidence.csv` says of each row how its label writes the name |
| Not every row that rests on the file with no receipt said so | `areas.csv` and `aliases.csv` say so in a column, and the item in a line |
| The area with no name was offered no names at the desk | Its item shows the name it was grown from and the two nearest, each with its record and how far off |
| 22 seeds were moved to a town centre whose label only holds the name | All 22 are marked, with how far each was moved |
| The main borough of an area is by output areas, and one is a tie | `areas.csv` says every borough of an area with its output areas in each, and whether it is a tie |
| The least size came from a figure of the table of homes | The sum is taken out. 12 is a guess of its own, for the founder to set |
| "A label, with no place" was said of a record that lies outside the area | The line says that the record lies outside, and how far off |
| The flag "one publisher" stood beside two source ids | A line is labelled with the publisher and the product in words |

## 6. What looks wrong

One picture of London and one of each of five boroughs were looked at before the checks, with no basemap. The borders have not changed since. The five are the first and second in the order, the seventeenth, the twenty-fifth and the thirty-first.

| Looked for | Found | Counted |
|---|---|---|
| One piece | Yes by the generalised outlines, which the draft draws with. By the full outlines, which stop at mean high water, `lon-n0411` is in two pieces: 2 output areas are parted from the other 54 by 3.5 to 6.6 m of water | Six areas hold two output areas that face each other over tidal water 3.5 to 43.7 m wide: `lon-n0411`, `lon-n0655`, `lon-n0643`, `lon-n0354`, `lon-n0341`, `lon-n0098`. All are on one bank of the main river. The checker measured this. The draft does not |
| Compact | In part. Most areas are one blob. Their edges are ragged, because an edge is the edge of an output area | By the measure where a circle is 1 and a square 0.79, the median area is 0.25. 99 are under 0.2 |
| Of like size | No. 12 to 208 output areas. By homes, which a checker read under another use, 1,346 to 27,051: a range of twenty times | The ten largest hold 132 to 208 output areas. 19 areas are flagged as unlike their neighbours |
| The seed in the middle | Often not | 130 seeds stand in an output area at the edge of their area. 10 lie outside it |
| Borders along the tidal river | Yes. No area crosses it | 23 road links over the water are taken up |
| Borders along the river above the tide | Not known. No file the gate gives draws it | 57 areas hold an output area with no bank, in 6 boroughs |
| Borders along railways | Not known. No file the gate gives draws a railway | Not counted |
| Borders along roads, wards and boroughs | In part | 60 areas have under a quarter of their border along a borough line, a ward line or a main road |
| Borders that cut a town centre | Seen in every borough looked at | At a twentieth, a town centre that writes an area's name lies over a second area 46 times |
| Areas across a borough line | Common, and some lie mostly in the next borough | 169 areas. 109 have 5 or more output areas outside their main borough |
| Names that look like a street or a building | 7 areas, in 287 output areas. 29 areas lie beside them | Each has 6 points: 3 for a populated place and 3 for a town centre of another name |

What the pictures cannot show: whether a name is the one people use, whether a border is where people feel it to be, and anything about railways, parks or the river above the tide. Those are what the desk is for.

## 7. What the founder decides

**The order of the work.** Names first. Then the draft is made again from the answers. Only then borders. A border looked at before its neighbours' names are settled may be looked at twice.

| Decision | What turns on it | Where |
|---|---|---|
| Is one official publisher enough for a name | 333 areas. It is one decision | Section 13 of the design |
| May a draft rest on the town centres before they have a receipt | 355 areas. A person must state the edition and the period of the file | `snapshots.json` |
| Does a town centre give points only to a place whose name it writes or holds | 205 of 516 names put forward have points from a centre of another name. 95 reach the 4 points asked only so | `counts.json`, and the line `Points` of each item |
| May a record in the smallest box the file draws be a seed | 10 names put forward. 12 more hold a word for a built thing in a larger box | `names_to_look_at.csv` |
| May a seed be moved to a town centre whose label only holds its name | 22 seeds | The same |
| May homes be read for `gazetteer` | The least size of an area, its main borough, what is at stake, and sizes in homes. Until then 12 output areas is a guess | The registry |
| May sizes and green space inform a border | A checker read both under `scoring` to say what looks wrong. Nothing of either is in the draft | Section 6 |
| Is a slug made with a hyphen where a name has an apostrophe | 10 slugs. A slug is an address that lasts. The function is the first build's | `areas.csv` |
| Which draft the desk starts from: 488 areas or 351 | The smaller draft does not take out the names that look like a street | `draft/` and `draft-by-the-designs-rule/` |

**Rules that would save hours.** Each is the founder's to adopt, and none is adopted. A rule settles only what no rule before it settles. The items are listed in `rules_would_settle.csv`, and what could go wrong with each rule is in `rules_put_to_the_founder.csv`.

| Rule | Would settle | Hours |
|---|---|---|
| 1. A name put forward as an area is accepted when Ordnance Survey writes it at a point inside, the town centres write it letter for letter over the area, and it has no mark | 104 names | 1.3 |
| 2. The same, with a ward of its name over the area in place of the town centre | 127 names | 1.6 |
| 3. The same, with 50 road records or more that give it as their settlement | 16 names | 0.2 |
| 4. Another name is accepted as a smaller place inside, when Ordnance Survey writes it as a suburban area, a village or a hamlet at a point inside, and it has no mark | 109 names | 1.4 |
| 5. A mark that says only that a station of the name stands elsewhere, or that the name was put under another area before the borders were drawn, holds no name back from rules 1 to 4 | 40 names | 0.5 |
| 6. A name of the kind Other Settlement that no road, no ward and no town centre writes, and that holds a word for a street or a building, is not kept | 19 names, 7 of them areas | 0.2 |
| 7. A town centre's label of two names, or with a part in brackets, is not kept as a name | 23 names | 0.3 |
| 8. A border flagged only for lying in two boroughs, with under 5 output areas and under a tenth of them outside its main borough, is not offered as flagged | 39 borders | 5.2 |
| **All eight** | **438 names and 39 borders** | **10.7** |

The checkers counted 410 names by their own reading of a mark. The draft counts 438 by the marks it lists, and 39 borders as they did.

## 8. The hours the queues hold

At the pace of section 9 of the areas design. Nobody has timed it. A checker who sat at the desk found about 12 seconds for a name that shows nothing to weigh.

| Queue | Items | Flagged | Each | Hours | The design guessed |
|---|---|---|---|---|---|
| `names` | 780 | 613 | 45 s | 9.8 | 14, for 1,100 |
| `borders`, the flagged alone | 230 | 230 | 8 min | 30.7 | 16, for 120 |
| `whole` | 33 | 33 | 15 min | 8.3 | 8 |
| `know` | 33 | 0 | 5 s | 0.05 | 0.1 |
| **The fast route** | | | | **48.7** | **38.1**, and 4 more to open a licence and try the page |
| `borders`, with the 49 only the draft flags | 279 | | 8 min | 37.2 | |
| `borders`, the first 120 of the order | 120 | | 8 min | 16 | |
| `borders`, every area | 488 | | 8 min | 65.1 | 60, for 450 |
| The fast route, were all eight rules adopted | 342 names, 191 borders | | | 38.0 | |

The table holds no hour that the changes of section 5 are meant to spare, because none was in it. The checker who sat at the desk reckoned them: 2.6 hours of looking marks up in two files, 5.8 hours of hunting for what a flag found, 1.2 hours of placing a cell by its code, and 4.4 to 23.9 hours of borders looked at twice. None was timed. By the design's own rule the queues hold 775 names, 209 flagged borders of 351, and 45.9 hours.

## 9. How to make it again, and how to see it

```
BURRO_STORE_FOLDER=<the store> uv run python -m burro_pipeline.areas.draft_run --out <a new folder>
    add --ids <made/names/ids.csv of the last draft>   so that every place keeps its id
    add --decided <the desk's out/names.csv>            so that a name that was turned down is no area
    add --kept <a file of area_id>                      for an area that stays however small
    add --points 6 --publishers 2                       for the design's own rule
    add --work <a folder>                               to keep the copies of the files between runs
```

The folder then holds the curated files, `pictures/`, `made/` and `desk/draft/`. `about.txt` says what each is.

The review desk is in `tools/desk/`. Take the draft to it, which copies `desk/draft` to `data/raw/desk/draft` and fills the queues. Then start the desk:

```
make desk-take DRAFT=<the folder the draft was written to>
make desk KEEP=<a folder outside the repository>
```

When this report was written a step of the areas build laid the lines over the items after every fill. The desk has read `lines.csv` itself since, and that step is removed. The head of [the desk's design](../../design/desk.md) says in ten lines how to sit down at the draft.

The desk's own code, at commit 3703d73, filled four queues from this draft. Its own reader took every item once the lines were laid over them, and its own server answered for every queue, for an item of each and for a layer. Nobody has looked at the page in a browser.

**A person makes an area of another name by hand.** The desk cannot. The file of decisions may be written by hand, with the columns `area_id` and `answer`: `area` for a place that is to be an area, and `inside`, `same_ground`, `wide` or `drop` for one that is not. The id of every place is in `made/names/ids.csv`. The items of 11 areas say which two rows to write.

## 10. What is still wrong, and what was not done

The first five rows were asked of the desk's owner, and have been done since: [the desk's design](../../design/desk.md), section 11, says how, and gives the counts as they now are. Every count of this report is of the draft as the desk took it then.

| Still wrong, or not done | Why | Who |
|---|---|---|
| The page says Saved for an answer the desk will set aside | The page and `compile` are the desk's, and the draft changes neither | The desk's owner |
| 49 areas the draft flags carry no flag at the desk | The desk has no words for `seeds_close`, `follows_nothing`, `size_unlike_neighbours`, `two_pieces`, `both_banks`, `seed_outside` and `no_receipt`. The words are in `made/flags/rules.json`. Folding them into a flag the desk has would put the wrong words on the item | The desk's owner |
| The desk does not read `lines.csv` | Its fill makes the lines itself. `draft_items` lays the draft's over them, and must be run after every fill | The desk's owner |
| The desk offers all 488 borders, and has no key for the next flagged one | 258 items to skip by hand | The desk's owner |
| Names run by borough in the order of the alphabet, and other names come after all 488 areas | The desk puts names in order | The desk's owner |
| The area with no name cannot be answered at the desk | Its pick is empty, which the desk sets aside. A person moves its border, or turns it down by hand | The founder |
| A wide name is offered over the five areas nearest it, of which two hold nothing of it | What "covers" means for a wide name is not settled. 2 items | The founder |
| A run lists every folder of the store to find the file with no receipt | The store's own method lists the whole store. It opens no file of another source | The first build's owner |
| No second publisher for most names | Wikidata has no file. The gate gives it, and this part fetches nothing | Whoever writes the query |
| A step of `python -m burro_pipeline` | It would change the command line, its test and the list of names a public log may show | |
| A model that matches spellings | Section 7 of the design. Drafting by rules alone is slower, and not blocked | |
| The check that every live postcode falls in an area | The postcode directory is not in the store | |
| The border test of section 10 | It needs a ranking on real areas | |
| The pictures looked at again | The borders did not change | |
| The whole suite under 30 seconds | It took 34.6 seconds: 32.5 without any test of the areas, and 2.7 for the 574 tests of the areas | |

## 11. What the gate kept out, and what is missing

| Source | What it would have given | What would let it in |
|---|---|---|
| `wikidata-places-and-landmarks` | A second publisher for most names, the wide names, and names to split the largest areas by. The gate gives it. It has no file: nobody has written the query | The query is written and fetched |
| `hoc-library-msoa-names` | A second publisher with ground made of output areas, and a cut of 15% | The founder saves a dated copy of its licence |
| `ons-census-2021-housing-tables` | Homes: the least size of an area, its main borough, its centre, and what is at stake in homes | `gazetteer` in its uses, on the founder's say |
| `os-open-rivers` | The river above the tide, as a barrier and as a line on a reviewer's map | `gazetteer` in its uses |
| `os-open-greenspace` | Parks on a reviewer's map | `gazetteer` in its uses |
| `dft-naptan` | Stations on a reviewer's map | `gazetteer` in its uses, and London's file saved by hand |
| `gla-high-street-boundaries` | A second anchor for a seed | A written reply from its owner |
| `osm-geofabrik-greater-london` | Nothing that may be used. It was not opened | Nothing. ADR 0004 |
| A receipt for `gla-town-centre-boundaries` | A draft that a build could rest on | A person states the edition and the period of the file |

## 12. Credits

Every count on this page was made from a file of one of these publishers. The words are each publisher's own, as the licence registry holds them. The registry marks each as not yet verified against the publisher's page. Some hold `[year]` where the publisher's page gives a year to fill in: which year is the founder's to say, and none was made up.

| Publisher | Files | Credit |
|---|---|---|
| Ordnance Survey | OS Open Names, Boundary-Line and OS Open Roads | Contains OS data © Crown copyright and database right [year]. |
| Greater London Authority | Town centre boundaries | Greater London Authority - Contains public sector information licensed under the Open Government Licence v3.0 |
| | | Contains OS data © Crown copyright and database rights 2019. |
| Office for National Statistics | The lookup | Source: Office for National Statistics licensed under the Open Government Licence v.3.0 |
| Office for National Statistics | The boundaries and the centres of output areas | Source: Office for National Statistics licensed under the Open Government Licence v.3.0. Contains OS data © Crown copyright and database right [year] |

The Greater London Authority cannot warrant the quality or accuracy of the data. Its boundaries are indicative, as its page says. Section 6 gives a range of homes, which a checker read under another use. A home is a household at the census of 2021, as the statistics office counts it. Source: Office for National Statistics.
