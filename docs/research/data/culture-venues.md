# Culture nearby: what is built, and what it waits on

Written 2026-09-24. A dated snapshot, not a source of truth.

**Since this page was written** the founder has stated the period of the file, the part has its receipt, and the measure has been worked out on it: [what the real file gave](culture-and-community-on-the-real-file.md). What follows is as it stood before. Where the two differ, the later page stands.

**No figure of a real place is on this page.** When it was written none had been worked out: no file of places had been fetched by a step of the pipeline. Everything here was built and driven on a made-up file, laid out as the publisher's own pages say its file is, and on a stand-in for the publisher on the loopback address. No person has checked anything here.

[The first look at Overture Places](overture-places.md) opened a real file of the same release, outside the pipeline and with no receipt. Its extract was not read for this work. Its findings are what this work answers to, and section 7 says what was done about each.

Credit: Overture Maps Foundation, overturemaps.org. Records from Meta and Microsoft are under CDLA-Permissive-2.0, from Foursquare under Apache 2.0, and from AllThePlaces under CC0.

## 0. In short

| Question | Answer |
|---|---|
| What is it for | A person who asks for culture nearby. No release can answer today |
| What is counted | Museums, galleries, theatres, cinemas, music venues and libraries within 800 metres of home, in a straight line |
| From what | One file of Overture Maps Places, release `2026-09-23.0`. Registry id `overture-places`, approved for `scoring` |
| Can fetch take London's part of the file | Yes. It asks for the file's footer, and then for the bytes of the part and no other |
| Has it been fetched | No. Section 1 says what to fetch |
| How is the kind decided | By the most particular category of a record. Never by a name: no name is read |
| Does one institution with many records count once | Records of one kind within 25 metres of the first of them are one venue. Section 5 says what that misses |
| Which figure is put forward | None yet. The check of section 6 is built, and has no real file to ask |
| Is it in a release | No. Core names the measure for each square kilometre, so it is not among the measures of a build |
| What is for the founder | Section 9 |

## 1. The file, and what to fetch

| | |
|---|---|
| Release | `2026-09-23.0`, which the publisher's catalogue names as its latest |
| Files | 16 for the places of the world, each a Parquet file packed with zstd. None is of a country or a city |
| The one that holds London | File `00007`. Its box runs from -1.59 to 6.29 degrees east and from 40.38 to 62.69 degrees north. No other file's box meets the box taken |
| Its size | 728,373,349 bytes, 5,152,063 rows, 256 row groups |
| Its columns | `id`, `geometry`, `confidence`, `websites`, `emails`, `socials`, `phones`, `brand`, `addresses`, `names`, `sources`, `operating_status`, `basic_category`, `taxonomy`, `version`, `bbox` |
| Where that was read | The publisher's own catalogue, `stac.overturemaps.org`, which its guide to places links to. It was read as the JSON it is |
| The list | `fetch/lists/m2-culture.toml`, one item: `overture-places-london` |
| The command | `uv run python -m burro_pipeline fetch --list m2-culture` |
| How much arrives | Not known until the footer is read. The list allows 250 MB. The first look read about 128 MB for a box of this size, of more columns |

The list states the period as the day of the release, and says it is not sure of it. So a first fetch keeps the part and writes no receipt, as for every file whose period no person has stated. The first look found that most records of one of the publisher's sources were last changed in 2019 or before, so the day of a release is not plainly the day its places are as at.

**The box.** West -0.53, south 51.28, east 0.33, north 51.71. The centres of London's 26,369 output areas were read through the licence gate in the file of centres of the first build. The box is their span and 2,000 metres more on every side, rounded outward. A test on the real centres holds the box to that.

## 2. Taking part of a file

A Parquet file ends with a footer that says where each column of each row group lies, and the least and the most of what it holds. Fetch reads the footer with the standard library alone, works out which bytes the part is, and asks for those a piece at a time.

| Step | What is asked of the publisher |
|---|---|
| 1 | The last 8 bytes of the file, which give the length of the footer. The answer gives the size of the whole file |
| 2 | The footer |
| 3 | Each run of bytes of the part, in the order of the file |

- **Which row groups.** A row group is taken unless the footer shows that no row of it lies in the box. It shows that by the least and the most of the box each row fits in. A row group with no least or most recorded is taken. So what is taken is every row in the box and the other rows of their row groups, and never the rows of the box alone.
- **Which columns.** Those the list names. No byte of any other column is asked for.
- **What is kept.** The publisher's own bytes, run after run: the four letters the file starts with, the columns taken of each row group taken, and the footer. Nothing is unpacked or written again.
- **The receipt** says which file, by its address and the size of the whole, what was wanted, which row groups of how many, and where in the file each run lies. Its hash is of the runs. So the same part taken again is the same bytes, and a part in the store is held to its receipt with no connection: the footer is in the part, so the plan is worked out again from the part alone.
- **One file.** Every piece must say that it is the bytes asked for, of a file of the size the first piece gave. Where the publisher marks the version of the file, each later piece is asked of that version.
- **Taken again later.** The receipt holds what a person needs to take the same bytes again: the address, the size of the whole file, and each run as its first byte and how many. Each run is asked for by itself, the answers are put one after another, and their hash is the hash of the receipt. No command does this from a receipt: `fetch` works the part out again from the list, which by then names a later release. The receipt does not hold the mark the publisher gave the version of the file, so a file that has changed is known by its size or by the hash, and only once the runs have arrived.
- **Whether the file will still be there.** The publisher's catalogue, read on 2026-09-24, names two releases and no more: `2026-08-19.0` and `2026-09-23.0`. Whether a release stays at its address once later ones are out is not known. Where it does not, the part cannot be taken again, the copy in the store is the only one, and its receipt is held to that copy alone.

What is refused, each with a number of its own, and nothing kept:

| `why=` | What happened |
|---|---|
| 36 | The publisher gave no piece: it answered with the whole file, or with other bytes |
| 37 | The file changed while pieces of it were taken |
| 38 | The file is not laid out as the list says: no Parquet file, a column missing, no box |
| 30 | The part, or its footer alone, is over the size the list states |

The footer is kept whole. It holds the least and the most of every column as the publisher's writer recorded them, and for a column of text those are two of its values. So a footer may hold a name or two of a place, from anywhere in the file, though no row of a name is taken. No step reads them, and what fetch reads of a footer keeps the least and the most of a column of numbers and of no other.

## 3. What is taken of a record, and what is not

| Taken | For |
|---|---|
| `geometry` | The point |
| `bbox` | The box of the row, which the footer is asked about |
| `taxonomy` | What the record is |
| `operating_status` | Whether the file says the place has closed |
| `confidence` | How sure the publisher is that the place exists |
| `sources` | Which of the publisher's sources gave the record, which the licence registry asks to be kept |

`id`, `names`, `addresses`, `phones`, `websites`, `socials`, `emails` and `brand` are not taken. `sources` is taken whole, and holds the id that the first publisher of a record gave it. The step asks for the one column in it that names the dataset, by its name in the file's own layout, and for nothing beside it, so the id is in the store and is never unpacked. A list can name one column inside another, and take that alone, and the step reads such a part as it reads one that holds `sources` whole. How the file names the columns inside `sources` is not known until its footer has been read, so the list cannot do so yet.

## 4. The kinds

The most particular category of a record decides: `taxonomy.primary`. The table is `derive/culture_kinds.py`.

| Kind | The publisher's categories |
|---|---|
| Museum | `museum`, and the 21 under it: `art_museum` and the nine under that, `aviation_museum`, `childrens_museum`, `history_museum` and the two under it, `military_museum`, `national_museum`, `science_museum` and `computer_museum`, `sports_museum`, `state_museum` |
| Gallery | `art_gallery` |
| Theatre | `theatre_venue` |
| Cinema | `movie_theater` |
| Music venue | `music_venue`, `jazz_and_blues_venue`, `opera_and_ballet` |
| Library | `library` |

What is left out, though its parent says otherwise:

| Category | Its parent | Why |
|---|---|---|
| `performing_arts_venue`, `arts_and_crafts_space` | | Each is a parent alone. It says no kind |
| `band_orchestra_symphony`, `choir` | `music_venue` | A group of players or singers, and no place |
| `karaoke_venue` | `music_venue` | A bar where the guests sing |
| `dinner_theater` | `theatre_venue` | A place to eat that puts on a show |
| `drive_in_theater`, `outdoor_movie_space` | `movie_theater` | A screen out of doors |
| `amphitheater`, `cabaret`, `comedy_club` | `performing_arts_venue` | None of the six kinds |
| `artist_studio`, `glass_blowing_venue`, `paint_and_sip_venue`, `paint_your_own_pottery_venue`, `sculpture_park`, `sculpture_statue`, `street_art` | `arts_and_crafts_space` | A place of work, a workshop, a park or one work of art |

- **A record that also says it teaches is left out.** The first look found that half the records under theatre are stage schools, by their names. A name is not read. A record whose most particular category is a kind, and which gives a category of a place of learning beside it, is left out. How many stage schools that catches is not known: it catches those the file itself calls a school.
- **A category of culture that the table does not hold stops the build.** It is never counted by a guess and never dropped by one. That holds of a category that stands under a parent the table reads. A kind that the file writes in other words, under another parent, is read as no record of culture and nothing stops. So a test on the real file holds that every one of the six kinds is found in the part.
- **What is left out is counted**, by the reason and by the category.
- **No place of worship and no cultural centre is counted.** The publisher files both apart from the arts.

Where the table comes from: the publisher's own table of categories for the release, read through a reader that extracts the text of a page. The branch of the arts was given the same by two answers, and the branch of education by one. The table was read as far as its branch for health care. No file has been opened to hold the table to.

## 5. The measure

Three figures for every area, by `derive/culture_venues.py`:

| Figure | Its id | Unit |
|---|---|---|
| Venues within 800 m of home, as the mean over homes | `culture_venues`, core's | count |
| Venues for each 1,000 homes within the same reach | `culture_venues_per_homes` | per 1,000 homes |
| How many of the six kinds are within 800 m of home | `culture_kinds_nearby` | kinds |

- **Reach, weights and the edge of London** are in `derive/culture_reach.py`, once, for any measure of places that are points. A test refuses a second module of `derive/` that measures a distance on the ground or says where London ends.
- **One venue with many records.** Records of one kind within 25 metres of the first of them are one venue, and the first is the one furthest west. Five records of one kind on one spot count once. An institution whose records stand further apart counts more than once: five records of one kind in a row 12 metres apart count as two. An institution whose records are of more than one kind counts once for each kind: a museum whose records are three of a museum, one of a gallery and one of a library counts as three. Two venues of one kind within 25 metres of each other count as one: ten galleries in a row 20 metres apart count as five. To do better needs the name or the website of a record, and neither is taken. The third figure does not turn on it: a kind is within reach or is not.
- **Nought.** Nought is read as a count only where the file holds a record of any kind within the same reach. Where it holds none, the output area has no count and the coverage of its area falls. Whether one record is enough is not settled.
- **The edge.** The part that is fetched reaches 2,000 metres beyond London's homes, so a venue outside London within reach of a home is in it. The homes outside London are in no file of the build, so the rate cannot be given where they are within reach. The count could be. Both are left out there, so that the two stand on the same homes.
- **Nothing is left out for how sure the publisher is.** The number is kept with each venue. The first look found it usable for the records of one source only.

## 6. Does it say something

`derive/culture_check.py` holds each figure against three things, across the areas that have all of them, by rank correlation: homes per hectare, the distance of an area's homes from the middle of London's homes, and a count of every record of the file within the same reach.

A figure follows the centre where it stands in the order of how much is about, or of the distance from the middle, at 0.9 or more, by either sign. Where the count follows the centre and the rate does not, the rate is put forward. In every other case nothing is put forward and a person decides.

**It has not been asked of a real file.** On the made-up town it prints three lines of numbers and puts nothing forward. Until it is asked, every row the catalogue would hold says that the figure is not ranked on.

## 7. What the first look found, and what was done

| The first look found | What was done | What is left |
|---|---|---|
| Counts track how much is there, and the centre | The rate and the kinds are worked out beside the count, and the check says which follows the centre | The check on the real file |
| A zero cannot be trusted | Nought is a count only where the file holds something within reach | Whether one record is enough. It may keep nearly every nought in London |
| Kinds hold things that are not the kind | The most particular category decides, a parent alone is left out, and a record that says it teaches is left out | A sample of records looked at by a person |
| One institution has many records | Records of one kind within 25 metres of the first are one venue | Records further apart. Whether 25 metres is right |
| A small area's figure moves between releases | Nothing. One release is pinned | A second release, to measure it |
| One record can fall in two figures | A record has one kind, by its most particular category | Nothing, within culture |
| It cannot tell an open place from a closed one | A record the file says has closed for good is left out. The rest are counted, and the words beside the figure say so | A second source |

Of what the first look asked for before any figure is shown: official boundaries are used, the rules for each kind are written, a rule for nought is written, and the test against density is built. The check of 20 areas against a register has not been made.

## 8. The catalogue's entry for culture

Core's catalogue holds one feature of culture, and it does not say what is built.

| Core says of `culture_venues` | What is built |
|---|---|
| Label "Theatres, cinemas, galleries, museums, libraries and music venues" | The same six kinds. The label does not say within what distance, or that it is a straight line |
| Unit `per km²` | A count within 800 metres of home. No figure for each square kilometre is worked out |
| Ranked on, and counted in likeness | Not put forward to be ranked on until the check has been asked of the real file |
| One feature | Three figures. Core has no feature for the rate or for the kinds |
| 15 in 100 of Pace | Which figure Pace takes is not decided |

What the entry needs, and the catalogue is not changed here:

1. A unit and a label for the count that say within 800 m of home, in a straight line.
2. A feature for the venues for each 1,000 homes, `culture_venues_per_homes`, and one for the kinds, `culture_kinds_nearby`, which the design of the vibes names.
3. Which of the three a wish for culture is ranked on, and which Pace takes, once the check has run.
4. A place for the lines shown beside a figure: `CANNOT_SEE` in the measure's module holds them.

## 9. What is needed

| # | What | Whose |
|---|---|---|
| 1 | Fetch the part: `fetch --list m2-culture`. Then state the period in the list, and fetch again for the receipt | The founder's |
| 2 | Whether the day of a release is the period of its places | The founder's |
| 3 | The check on the real file, and with it which figure is put forward | Follows 1 |
| 4 | A sample of records of each kind looked at by a person, to hold the table of kinds to | The founder's |
| 5 | Whether 25 metres is right for one venue, and whether a name may be read to match the records of one institution and for nothing else | The founder's |
| 6 | Whether one record of any kind within reach is enough for nought to be a count | The founder's |
| 7 | Whether a record is left out for how sure the publisher is, and at what number | The founder's |
| 8 | The choices of section 4: opera and ballet as a music venue, a comedy club and a cabaret as none of the six, a cinema out of doors as none | The founder's |
| 9 | Core's entry for culture: section 8 | Core's |
| 10 | The check of 20 areas against a register, which the first look asks for | Nobody has |
| 11 | Narrow `sources` in the list to the name of the dataset alone, once the footer of the real file has been read | Follows 1 |
| 12 | Whether the publisher keeps a release at its address once later ones are out. If it does not, where a second copy of the part is kept | The founder's |
| 13 | Whether a venue keeps the number of its first record for how sure the publisher is, or the greatest of its records. It matters once a record is left out by that number | The founder's |
| 14 | Whether a record is left out, or the build stops, where it names a dataset that the registry entry does not. Today every dataset is counted, and the count by dataset is there to be read | The founder's |

## 10. What was not done

- No real file of places was opened, so no count, no figure and no correlation of London is known.
- The table of kinds was not held to a file, and was read through a reader that extracts.
- The measure was not added to the measures of a build, and no release carries it.
- The publisher's copy of the file on Azure was not listed.
- Nothing was done about a figure that moves between releases.
