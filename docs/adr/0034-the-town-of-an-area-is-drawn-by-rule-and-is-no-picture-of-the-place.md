# 0034. The town of an area is drawn by rule from four bands, and is no picture of the place

Status: accepted, 2026-09-26, as part of the look ([0033](0033-the-website-looks-like-the-map-of-a-gentle-game.md)). That an area has a little town is the founder's, from Town Map. The rule it is drawn by, every word it says and the key beside it were made in the building, and each is the founder's to overturn: the last section says which. **Amended the same day**: a town stands beside the name of every result that has room for one, and over a list of results its line is said once. **And again, later that day**: the town of a result is drawn from where the page holds that its area sits, and no longer from its strip alone, so that a part of it is blank for what is not known and never for what was not asked for. **Amended once the founder had walked the website**, that day: the key of a town stands inside the key to every drawing of the website, first on the page of vibes, and the words of its line were written again. What a town is drawn from, what it leaves blank and what it may never show are as they were. See "Amended, 2026-09-26: the key, and the words of the line", below. **Amended again that evening, once the founder had walked the website a second time**: the line is gone from a list of results, from the bar of areas to compare and from the head of a comparison, and a town stands there with no line beside it. It stays at the head of the page of an area and in the key. Until then this record was named "The town of an area is drawn by rule from four bands, and says that it is no picture of the place". See "Amended again, 2026-09-26: a town of a result stands without its line", below, which says what that gives up.

## Context

Town Map drew each area as a little town: a few buildings and trees on a sod of meadow. It is the touch of the look that says most of a place, and so the one that can say most that is untrue. Burro shows nothing of a place that does not trace to a stored fact with a source and a date (rule 6), gives no verdict of a place, and ranks places and never residents ([0006](0006-rank-places-not-residents.md)). A drawing of homes beside the name of a real place may be taken for a picture of it.

Town Map also drew the whole city as towns on a grid. That is not taken: the map is the real border of every area.

## Decision

**The town of an area is a drawing made by one rule from where the area sits on four vibes. It is not a picture of the place, and it says so in sight wherever it is drawn.** *Since the evening of 2026-09-26 it says so at the head of the page of an area and in the key, and no longer beside a result or in the bar of areas to compare.*

| Matter | What is so |
|---|---|
| What it is drawn from | Four bands, each one of five, as the service gives them. One vibe is its trees, one the height of its buildings, one its lit windows and one its roofs. In the releases of today they are Leafy, Houses or flats, Going out and Age of buildings. One table names the four by their ids, `DRAWN_FROM` in `apps/web/src/lib/town/vibes.ts`, and no other file of the town names a vibe |
| What it is handed | The bands, the names the service gives the vibes and their ends, and the name of the area, which is said to a screen reader and never drawn. It is handed no rank and no fit, and its types refuse one. So two areas with the same four bands are one picture |
| The line | "Drawn from four of this area's vibes. Not a picture of the place." It stands with a town, in sight, in the reading face and in ink. Over a list of results it is said once, over the list and of every town of it: "Each town is drawn from four of its area's vibes. Not a picture of the place." A town never stands without the one or the other |
| What it says to a screen reader | What it is, and each of its four parts band by band, in the service's name for the vibe and its ends |
| Its size | One size for every area, the first result as the tenth: 56 art pixels by 32. It is drawn at two pixels of the screen to one of its own, 112 by 64, so that it is no larger than the name it stands beside. Beside the title of a page it may be drawn at three, and on a result 39rem wide or wider |
| What it is not | It has no frame and no shadow: a framed picture at the head of a listing is, everywhere else, a photograph of the place. Nothing of it moves, and it cannot be pressed |
| The key | What each part is drawn from, with a town at each end of it, and a town of which nothing is known. It stands once on the page of vibes and once on the page of methods. **Amended on 2026-09-26**: it stands inside the key to every drawing, first on the page of vibes |

The rule, which is `planOf` in `apps/web/src/lib/town/plan.ts`:

| Part | Band 1 | Band 5 | Between |
|---|---|---|---|
| Trees | One tree | Five | One more with each band |
| Height | Four houses | Four blocks | With every band some building is taller and none is lower |
| Lit windows | One window of the town | Every window | A quarter, a half, three quarters, shared among the buildings |
| Roofs | Every roof newer | Every roof older | One more older with each band |

**What is left blank.** Where Burro cannot place an area on one of the four, that part is not drawn: no tree, and a ring of dots where one would stand; no building, and four plots marked out in dots; every window dark; no roof, and the wall closed by a line of dashes. *Since the afternoon of 2026-09-26 no line of a drawing is drawn in pieces: the ring, the plots and the line that closes a wall are each one whole line of shade.* Under the line the town says which part is blank and why. Every band draws something of its part, the least among them: one tree, one lit window. So a part with nothing in it can only say that nothing is known. What is not known is never drawn as the middle, and never as the least (rule 7).

**What it may never show.**

| Never | Why |
|---|---|
| A rank, a fit, or anything that says one area has done better than another | A vibe is a taste. A tall town is not a better town, and neither end of a vibe is the good end |
| Recorded crime | Recorded crime is shown only where a person asks for it, and nobody asks for a town. Should a release give one of the four a recipe that holds it, that part is left blank whatever the band, and says why |
| A person, or anything that says who lives there | Rule 8. A town is buildings and trees |
| The name of the area, in the drawing | A name in a picture cannot be held to the service's |
| A thing of the place itself: a church, a bridge, a river, a shop | The data holds none. A part stands for a band, and a band is five steps of a measure |
| A vibe that is a rough guide, unsaid | It says so under the line, in the service's words, as it does wherever it is shown. *Overturned on the evening of 2026-09-26: no page of the website says that a vibe is a rough guide ([0013](0013-vibes-are-the-centre.md), as amended), and a town says nothing of it* |

**The town of a result.** Amended on 2026-09-26.

| Matter | What is so |
|---|---|
| Where it stands | At the far end of the heading of a result, after the rank, the name and the fit, which are read first and heard first. On a card and on a row alike |
| Which results have one | Every result that has room for one beside its name and its fit: a result 36rem wide or wider, which a result is on a desktop. A result with no room has none, and its list has no line. Every result of a phone is one: with a town and the line, the first result of a plain search stood from 519 to 921 px of a screen 844 high, and the answer comes first |
| The line | Once, over the first part of the list, in a slip of cream. No town of the list says it again: under ten towns it is the same words ten times. What a town leaves blank, and why, is said with the town, under the heading of its result |
| What it is drawn from | Where the area sits on the four vibes, as the page holds it. The search page and the page a shared link opens are each built with where every area sits, from route 4, and hand it to the list. What the strip of the result says of a vibe comes first, so that a town and the strip beside it never say two things of one area. So a result and the page of its area draw one town, whatever was searched for, and a part of it is blank only where the area has no band for its vibe |
| What it is handed | The area, its strip and where every area sits, and neither its rank nor its fit. Nothing is asked of the service for a town |
| Three lines choose | `TOWN_DRAWN`, `LINE_STANDS` and `ON_A_NARROW_RESULT`, in `apps/web/src/components/ResultList/look.ts`: how large, the line once or under each town, and whether a narrow result draws a town all the same |

What was weighed, and put aside:

| Way | Why not |
|---|---|
| The town of a result drawn from its strip alone, as it first was | A strip holds what was asked for and two more, and a town is drawn from four vibes: of 983 recorded results none holds all four. Every town then had a part left blank and said of it that it was not known, which was untrue of the area: the release held it, and the page of the area drew it. And the town of an area changed with the search. A blank is for what is not known, and never for what was not asked for |
| The line under the town of every result | It is built, and one line chooses it. Under ten towns it is the same words ten times |
| A town on a result of a phone | It is built, and one line chooses it. The name, the fit and what stands beside the name then have a line each, the heading is 28 px higher, and the first result ends under the first screen |
| Two towns of the same four bands drawn differently, by the name of the area, as Town Map drew them | The name would then move the picture, and a picture that differs says that the places differ |
| No tree for the least leafy band, and no lit window for the calmest | A bare plot would say either that the area has least, or that nothing is known of it |
| Trees as tall as the buildings | They hid windows. Every window the rule lights can be counted in the picture |
| A mixed area, which spans three bands or more, drawn blank | It is drawn from its band, and its words say that it varies and which band it is drawn as. A town is no line of five, and the middle bands of a town are mixtures already |
| The parts written out under every town | Under ten towns of a list it is forty lines. They are said to a screen reader, and written out where the page asks for it |

## Consequences

- **A town stands at the head of the page of an area, at the head of each area of a comparison, and beside the name of every result that has room for one.** On a phone no result has one: the first result has 16 px to spare there, and a town is 64 px high.
- **On a preview most towns are poor drawings.** A preview places areas on few vibes, so a town of it is houses or blocks with dark windows, no roof and no tree, and says which parts are blank. It is true.
- **The words are new site copy**, in `apps/web/src/content/town.ts`, and nobody has reviewed them.
- **Every piece of a town is a drawing of the website's own**, laid by `apps/web/src/lib/town/pieces.ts` and by no other file. A test puts the picture together pixel by pixel from the text of the drawings, and counts in it what the rule said.
- What holds it: `test_it_never_stands_without_the_line_that_says_it_is_no_picture_of_the_place`, `test_the_rule_takes_the_four_bands_and_nothing_else_so_no_name_rank_or_fit_can_move_it`, `test_a_part_that_is_not_known_is_drawn_as_no_band_of_it_is_never_the_least_and_never_the_middle`, `test_a_vibe_whose_recipe_holds_recorded_crime_is_not_drawn_whatever_band_the_area_has`, `test_no_file_of_the_town_but_the_table_names_a_vibe_by_its_id`, `test_it_can_be_neither_pressed_nor_given_the_focus`, and `test_nothing_but_the_town_and_its_key_draws_a_town_with_no_line_beside_it`, which reads the source of the whole website. Of a result: `test_the_line_that_says_what_a_town_is_stands_once_over_the_list_in_sight_and_no_town_says_it_again`, `test_no_line_stands_where_no_town_does`, `test_a_town_is_of_one_size_on_the_first_result_as_on_the_tenth_and_says_nothing_of_a_rank_or_a_fit`, `test_handed_where_every_area_sits_the_town_of_a_result_is_the_town_of_the_page_of_its_area`, and `test_a_result_with_no_room_for_a_town_has_none_and_its_list_no_line_so_that_the_first_result_is_whole_on_the_first_screen_of_a_phone`. Of the page that hands it down: `test_the_town_of_a_result_is_the_town_of_the_page_of_its_area_whatever_was_searched_for`, `test_a_part_of_a_town_is_blank_for_what_is_not_known_and_never_for_what_was_not_asked_for`, and `test_the_town_of_a_result_of_a_shared_search_is_the_town_of_the_page_of_its_area`.

## Amended, 2026-09-26: the key, and the words of the line

The founder walked through the website, and wrote of the pages that explain: "A key to the visuals/icons is valuable, and should be expanded", and "The what a town is built of is also useful, mix in with the visuals/icons section."

| Matter | What was decided | What stands now |
|---|---|---|
| Where the key of a town stands | Once on the page of vibes, after every vibe and after how a band is drawn, and once on the page of methods | Once, inside the key to every drawing of the website, which is the first thing on the page of vibes ([0040](0040-a-page-that-explains-leads-with-a-key-and-folds-its-working.md)). It says what a town is built of: its trees, the height of its buildings, its lit windows, its roofs, and what a blank means. It no longer stands on the page of methods |
| Where a town stands | At the head of the page of an area, at the head of each area of a comparison, and beside the name of every result that has room for one | The same, and in the bar of areas to compare, by the name of each area that is chosen, where the screen has the width for it ([0039](0039-comparing-areas-is-a-headline-of-the-website-and-nobody-wins-a-comparison.md)). Where towns stand together the line is said once, of every one of them |
| The words of the line | "Drawn from four of this area's vibes. Not a picture of the place.", and over a list of results "Each town is drawn from four of its area's vibes. Not a picture of the place." | Written again, as [the guide to the words](../design/words.md) asks: in whole sentences that are joined. What the line says is as it was, and both halves of it: what a town is drawn from, and that it is no picture of the place. The words are in `apps/web/src/content/town.ts` and `towns.ts` |
| Everything else of this record | | As it was: the rule, the four vibes, what is left blank, what a town may never show, its size, and that it never stands without its line |

A town never stands without its line, and the line never says less than it did. A sentence that reads better and leaves out that a town is no picture of the place has broken the one promise this record was written for.

## Amended again, 2026-09-26: a town of a result stands without its line

The founder walked the website a second time, that evening, and wrote: "remove the 'each little town' disclaimer on the ranking cards."

As the website was mended after the first walk, the line of a list of results stood once, under the heading of the first result, where it had stood in a slip over the list: the slip, which held it with what says that areas can be compared, cost the first result 74 px of a wide screen. In the bar of areas to compare it was said once, in short, and at the head of a comparison once, before the first of the towns.

| Matter | What stood since that afternoon | What stands now |
|---|---|---|
| A list of results | The line stood once, under the heading of the first result, and was said of every town of the list | No line. A town stands at the far end of the heading of a result that has room for one, as it did, and nothing beside it says what it is |
| The bar of areas to compare | The line was said once in the bar, in short, of every town of it | No line |
| The head of a comparison | The line was said once, in sight, before the first of the towns | No line. A person comes to a comparison from the results, and it stood there in the same words, of the same towns |
| The head of the page of an area | The line under the town, and in one sentence on a narrow screen, which says both things: what a town is drawn from, and that it is no picture of the place | The same |
| The key to the drawings, first on the page of vibes | What a town is built of, with the line at its head | The same |
| What a town says to a screen reader | What it is, "A little town, drawn from four vibes", with the name of its area, and each of its four parts band by band | The same, on a result as everywhere: whoever hears a town is still told what it is drawn from |
| Everything else of this record | | As it was: the rule, the four vibes, what is left blank, its size, that it has no frame and no shadow, and what a town may never show |

**What it gives up.** This record was written for one promise: that a town never stands without the line that says it is no picture of the place. On a result, in the bar and at the head of a comparison it now does. A person who opens a list of results sees a drawing of homes and trees beside the name of a real place, and nothing in sight says that the drawing is made by rule. They may take it for a picture of the place.

**The test that held the line to a list went with it.** This record names `test_the_line_that_says_what_a_town_is_stands_once_over_the_list_in_sight_and_no_town_says_it_again`, which held what is no longer so of a list. `test_it_never_stands_without_the_line_that_says_it_is_no_picture_of_the_place` stands: it is of a town that is drawn by itself, as at the head of the page of an area. That one line of the look puts the line back is held beside each part, as by `test_one_line_of_the_look_has_the_line_stand_once_where_the_first_town_is_and_no_town_says_it_again` and `test_one_line_of_the_look_has_the_bar_say_once_what_a_town_is_and_only_where_a_town_stands`.

**What holds it.** The drawing is as it was decided so that it would not be taken for one: small, of one size for every area, with no frame and no shadow, where a framed picture at the head of a listing is a photograph. It is built of a few pieces that every town shares, so two towns of a list are plainly of one kind. The name of a result leads to the page of its area, where the line stands under the town, and the key to the drawings says it of every town. No test holds any of that to what a person takes a town for: it is seen by asking people.

What was weighed, and put aside:

| Way | Why not |
|---|---|
| The line kept on the first result alone, in fewer words | The founder asked for it to go from the ranking cards |
| The line kept in the bar of areas to compare and at the head of a comparison, since the founder named the cards | The bar stands over a list of results, and a comparison is reached from one. Each said of the same towns what the list no longer says |
| The town taken off a result with its line, so that none stands without it | The founder asked for the line to go, and not the town |
| The line taken from the page of an area and from the key too | The founder asked for it to go from the ranking cards. Where a page is about one area, or explains a drawing, the line is what a person came to read. It is the founder's to overturn |

## What would change it

| If | Then |
|---|---|
| A town is taken for a picture of the place, by a person who writes in or by a review | It is taken off the page it was seen on: [the design of the look](../design/look.md) says how. Nothing else depends on it |
| The line over a list is not read as the line of each town | `LINE_STANDS` is `each`, and the line stands under every town. *No line stands with a list since the evening of 2026-09-26* |
| The founder wants the line back beside a result, in the bar or at the head of a comparison | One line for each, under `apps/web/src/components/`: `LINE_STANDS` in `ResultList/look.ts`, `BAR_SAYS_OF_ITS_TOWNS` in `CompareTray/look.ts`, and `HEADS_SAY_OF_THEIR_TOWNS` in `CompareTable/look.ts`. The words are kept |
| The founder wants another vibe to stand for a part | One line of `DRAWN_FROM`. A vibe that counts recorded crime, or who lives somewhere, is never one of the four |
| The founder wants the rule otherwise: which building is tall in which band, how many windows a band lights | One table of `plan.ts` for each |
| The service comes to serve a thing of the place with a source and a date, as a landmark would be | It is a new decision whether a town may hold it |
| The founder holds that a mixed area should be drawn blank | `bandsOf` in `bands.ts` gives no band for an area that spans three bands or more, and its words say that it varies |
