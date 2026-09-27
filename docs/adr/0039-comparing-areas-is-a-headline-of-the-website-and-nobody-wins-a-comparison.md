# 0039. Comparing areas is a headline of the website, and nobody wins a comparison

Status: accepted, 2026-09-26. The founder asked for it, once they had walked the website. Where the way to compare stands, what it says and how the bar of areas is drawn were set in the building, and are the founder's to overturn: the last section says which. **Amended that evening, once the founder had walked the website a second time**: a comparison has a way back to the search at its head, and the bar of areas says nothing of what a town is. See "Amended, 2026-09-26", below, which says first how comparing stood when the founder walked it that second time. **Amended on 2026-09-27, once the founder had walked the website a third time**: a result says why it fits in no sentence, the gauge of a vibe in a comparison has a picture at each end and no words under it, and a fit that is not whole says "approx data" where a warning sign stood. Three things were decided as it was built, and are the founder's to overturn. See "Amended, 2026-09-27", below.

## Context

- A comparison sets two to four areas side by side: where each sits on each vibe, and then each thing that counts in the search that is open, with one row for each journey. It was built with the page of an area, and is an address of its own.
- The way to it was the third of three buttons at the foot of a result, named "Compare", and a button under the town on the page of an area. The bar that gathers the areas took no room until an area was chosen, so that the answer comes first. So nothing on a page said that areas can be compared, until a person had found the button and pressed it.
- The founder walked through the website, and wrote: "Compare function is great, make this more of a highlighted feature".
- Two areas side by side ask which is the better. Burro gives no verdict of a place, and in the look nothing is won ([0033](0033-the-website-looks-like-the-map-of-a-gentle-game.md)). A comparison is where a verdict is nearest.
- Once a ranking follows a press the first result is in sight, and on a phone it is whole on the first screen ([0035](0035-the-search-page-is-one-box-and-the-look-gives-way-to-the-answer.md)). Whatever is added over a result, or into its heading, stands in that room.

## Decision

**That areas can be compared is said, shown and reached before anybody has chosen one. It is highlighted as a thing to do, and never as a verdict.**

| Matter | What is so |
|---|---|
| That it can be done | Said in a sentence, before any area is chosen: a person chooses two to four areas, and Burro sets them side by side. The sentence names the button as the button names itself. It stands over the list of results on a screen that has room for it, and under the first result on a narrow one, so that nothing more stands between the box and the answer there. Two small drawings of the look stand with it, of lower homes and of taller: they are dress, and say nothing of any area |
| On a result | The way to compare is the most visible of the three ways on. It stands in the heading of the result, by its town, and not at its foot. It says what it does, "Add to compare". Once its area is chosen it is amber and says "Added to compare", and a press takes the area out again. It is drawn the same on every result, the first as the tenth. On a narrow result it is as high as a small button of the look, 34 px, so that it costs the first result of a phone no height |
| On the page of an area | At the head of the page, by the town, as plain as on a result |
| The bar of areas | A box of the look, at the foot of the screen, which takes no room until an area is chosen. It has four places, which is the most a comparison takes. Each area that is chosen has one, with its town, its name and the cross that takes it out again, in the order they were chosen and in no other. Each place that is left is kept empty, so that the bar is as wide with one area as with four and nothing in it moves as an area is added. A town is drawn where the screen has the width for it. It holds one button, which is cobalt. With one area chosen it says what to do next, which is to choose one more. With two to four the button says how many it compares, as "Compare 2 areas". What a town is, and is not, is said once in the bar, of every town of it. An area of which nothing was handed to draw a town from has none: a town left blank would say that its parts are not known |
| The comparison | At its head stands each area, with its town and its name, all of one size. Then where each sits on each vibe, side by side on every screen, which is what a person came for, before anything else |
| Nobody wins | Nothing marks one area of a comparison as the best: no colour, no size, no order and no word. Where a search is open each area says its rank and its fit from that search, as it did, and no more is made of either |
| The answer comes first | The way to compare costs the first result none of its place. On a phone no town is drawn on a result, as before, and the first result is whole on the first screen |

What was weighed, and put aside:

| Way | Why not |
|---|---|
| The area that fits best marked in a comparison, or set first | It is a verdict. Nothing is won, and the pennant of the first result is the pennant of the tenth |
| A town on every result of a phone, so that the way to compare has its town by it | A town is 64 px high, and the first result of a phone had 16 px to spare ([0034](0034-the-town-of-an-area-is-drawn-by-rule-and-is-no-picture-of-the-place.md)) |
| The way to the comparison in cream, so that a page holds one cobalt button | It was so, and among the many buttons of a page that are drawn in cream the one that compares was not seen. It is cobalt, at the foot of the screen, and Search is cobalt at the head of the page: the two are never side by side. It is built both ways |
| The way to compare left at the foot of a result, and made larger | The eye goes to the heading of a result: its rank, its name, its fit and its town. A person who reads no further than that never met it |
| What says that areas can be compared, over the first result of a phone | The first result is whole on the first screen there, and nothing is put between the box and it. Where the line stands on a wide screen is built three ways, and one line chooses |

## Consequences

- **What was measured of a result and of the bar was measured again on 2026-09-26, of the website as it stands.** The heading of a result is 112 px high on a desk with the way to compare in it, and 64 to 69 on a phone. After a plain search the first result of a phone ends at 838 of 844, whole. With a town for each area the bar is 111 px high on a phone with one area, 116 with two and 160 with three or four, and on a desk 123.5 with one and 129.5 with more. [The design](../design/web.md), section 4, has each.
- **A result says "compare" before it says why it fits.** What a result says was not changed, and the order in which a screen reader reaches its parts is in the design, section 4. *Since 2026-09-27 a result says why it fits in no sentence. The way to compare stands in its heading, as it did ([0046](0046-a-result-shows-what-was-asked-for-as-a-name-and-a-gauge-and-the-source-of-every-figure-stands-under-its-working.md)).*
- **The words are new site copy**, in `apps/web/src/content/compare.ts` and `card.ts`, written as [the guide to the words](../design/words.md) asks.
- **A test holds that every area is drawn as the next is, and none holds what is said.** `test_the_way_to_compare_is_drawn_the_same_on_every_result_because_nobody_wins`, `test_every_area_of_the_bar_is_drawn_as_the_next_is_because_nobody_wins` and `test_nobody_wins_a_comparison_every_area_is_drawn_as_the_next_is_whatever_its_rank` hold the drawing. That no word calls an area the better is read by a person, as the rule that nothing on a page is a prize, a score or a level is.
- What else holds it, in `apps/web/src/components/`: `test_the_button_says_add_to_compare_and_once_chosen_added_to_compare`, `test_what_says_that_areas_can_be_compared_names_the_button_as_the_button_names_itself`, `test_the_way_to_compare_stands_in_the_heading_of_every_result_beside_its_town_and_not_at_its_foot`, `test_one_area_is_not_enough_to_compare_and_the_tray_says_what_to_do_next`, and `test_the_bar_is_a_box_of_the_look_once_an_area_is_chosen_and_draws_nothing_until_then`.

## Amended, 2026-09-26

### How comparing stood when the founder walked it a second time

The website was mended that afternoon, and what that changed of comparing was written into no record then.

| Matter | What this record says | How it stood at the second walk |
|---|---|---|
| Where it is said that areas can be compared | Over the list of results on a screen that has room for it, and under the first result on a narrow one | Beside "Refine search", on its line, so that nothing stands over the list: over the list it stood the first result out of sight on a wide screen. Under the first result on a narrow screen, and where what stands over the answer gives way. `INVITE_STANDS` in `CompareTray/look.ts` chooses, with `OVER_THE_LIST` in `ResultList/look.ts` |
| What takes an area out of the bar | The cross of each area, and nothing that takes them all | The cross of each area. From two areas on, on a screen that has the line for it, a small way to take every area out at once, "Clear", which was in the bar as the founder first walked it. `CLEAR_STANDS` chooses |
| How many buttons are cobalt | Two with the bar in sight: Search, and the way to the comparison | The same, and a third while the panel that shares a search is open: the button that makes the link |
| What a comparison says of how much a thing counts | | As a weight, "Weight 50", with one line over the table that says what a weight is. That it is said as "Counts 50 of 100" is built too, and `COUNTS_SAID` in `apps/web/src/content/compare.ts` chooses |

### What the founder wrote

"Compare areas needs a back step, how do I get back to my search?" And of the towns: "remove the 'each little town' disclaimer on the ranking cards."

| Matter | What stood at the second walk | What stands now |
|---|---|---|
| The way back | At the foot of a comparison one button led to the search page: "Choose other areas" where a search was open, and "Go to the search" where none was. Nothing at its head led anywhere, and nothing said that the search was still there | At the head of the comparison, before anything else, "Back to your search". It leads to the search page with the search as it was left: what was asked for, what was set, the results, and the areas that are chosen to compare. Where the page holds no search, because the comparison was opened by its link alone, it says "Start a search", and leads to the first page |
| What keeps the search | The session, in memory, for as long as the tab is open. Nothing of a search is in an address or in the storage of the browser ([0011](0011-nothing-is-kept-for-a-search.md)) | The same. The way back is a link inside the website, so the session is there when it is followed. A comparison that is opened afresh, by its address, holds no search to go back to, and says so by what its way back is named |
| The line of the towns, in the bar and at the head of a comparison | Said once in the bar, in short, of every town of it, and once at the head of a comparison, before the first of the towns | Gone from both, as it is from a list of results ([0034](0034-the-town-of-an-area-is-drawn-by-rule-and-is-no-picture-of-the-place.md), as amended). A town still stands by the name of each area that is chosen, where the screen has the width for it, and at the head of each area of a comparison |
| A vibe that is a rough guide, in a comparison | Its label and its sentence under the name of the vibe | Neither ([0013](0013-vibes-are-the-centre.md), as amended) |
| Where five steps stand in the rows of a comparison | Wherever the name before them ended | In one column, as on a result, so that the eye runs down them |
| Everything else of this record | | As it was: that areas can be compared is said before one is chosen, the way to compare stands in the heading of a result and says what it does, the bar takes no room until an area is chosen, and nobody wins a comparison |

What was weighed, and put aside:

| Way | Why not |
|---|---|
| The way back as the browser's own, and no more | It was so, and the founder asked how to get back |
| The search put in the address of the comparison, so that a comparison opened afresh has one to go back to | A search is in no address ([0011](0011-nothing-is-kept-for-a-search.md)). The address of a comparison holds the areas and nothing else |
| The way back at the foot of the comparison, with the other ways on | A comparison of four areas is many screens long on a phone. What leads back is wanted where a person arrives |

## Amended, 2026-09-27

The founder walked the website a third time, late on 2026-09-26. Of comparing they wrote nothing. Of a gauge they wrote "where a gauge may exist, ensure they have a opposing icons for each side of the gauge", and of the words under one, "remove the explainer text under the gauges. we dont need that level of detail." A comparison is many gauges side by side, so what they asked of a result was built of a comparison too.

| Matter | What stood | What stands now |
|---|---|---|
| What a result says after the way to compare | Why it fits, and then its trade-off | Its lines and its trade-off. It says why it fits in no sentence ([0046](0046-a-result-shows-what-was-asked-for-as-a-name-and-a-gauge-and-the-source-of-every-figure-stands-under-its-working.md)). The way to compare is one of four things a result holds to press, where it was one of nine |
| Where an area sits on a vibe, in a comparison | Five steps with a peg, and beside them where the area sits in words a person would use, and its band | Its gauge: five steps with a peg, between the one picture of each end of the vibe. Nothing stands under it. Where the area sits is said in words by the name of the picture, to whoever hears the page |
| A band that rests on part of what its vibe needs | In the service's own clause, after the words that said where the area sits | The mark of what is not whole and "approx data". What the band rests on is on the page of the area, which the name of the area leads to |
| The head of the row of a vibe | The name of the vibe, which way its bands run, and its source | The small drawing of the vibe with its name, and the same |
| A fit that is not whole, at the head of an area | A warning sign in poppy, and the sentence that says how many of the things that count the fit is based on | The mark of what is not whole and "approx data", and then the sentence. Nothing of a comparison is poppy, and nothing warns |
| The two drawings beside the sentence that says areas can be compared | Two houses, and two blocks of flats | One house, and one block of flats, since each end of a gauge has one picture ([0033](0033-the-website-looks-like-the-map-of-a-gentle-game.md), as amended) |
| Nobody wins | No area is first, no figure is marked as the better, and no medal is drawn | The same. No picture at an end of a gauge says that the end is the better one, and the same two pictures stand at the ends of a gauge whichever area it is of |
| The bar of areas, where it comes over the button that was pressed | The bar came to stand at the foot of the screen as the first area was chosen, and where the button stood that low the bar lay over it. Measured at 1440 by 900: the button stood from 775 to 819, and the bar came from 776.5 | The button is brought clear of the bar, with what stands beside it on its line, and no further: the page goes by 51 px, and the button stands from 724 to 768. A button that stood clear is not moved. **It is the one press of the website that moves the page** ([0033](0033-the-website-looks-like-the-map-of-a-gentle-game.md) holds that nothing moves under a press), and is the founder's to overturn: `keepClearOf` in `apps/web/src/components/CompareTray/CompareButton.tsx` |

**Decided for the founder**, as it was built. Each is theirs to overturn, and the lines are in `apps/web/src/components/CompareTable/look.ts`.

| What was decided | Why | The line that chooses |
|---|---|---|
| **Nothing is said under a gauge of a comparison** | The founder asked for the words under a gauge to go from a result. A cell of a comparison is smaller than a line of a result, and holds the same gauge | `UNDER_A_GAUGE`, which is `nothing` or `words` |
| **The two pictures stand at the ends of the gauge of every area**, and not once at the head of the row | A gauge then says by itself what its ends are, as the gauge of a result does | `ENDS_STAND`, which is `gauge` or `row` |
| **What a band rests on is left to the page of the area** | The two words say that the band is not whole. A cell has no room for a sentence | None |

What holds it, beside the tables of a comparison in `apps/web/src/components/CompareTable/`: `test_the_small_drawing_of_a_vibe_stands_with_its_name_at_the_head_of_its_row`, `test_what_a_band_rests_on_is_left_to_the_page_of_the_area_whatever_its_fact_says_of_it`, `test_a_fit_that_rests_on_part_says_approx_data_after_the_mark_of_what_is_not_whole_and_nothing_of_it_warns`, and `test_the_steps_of_a_gauge_are_as_wide_as_its_cell_has_the_room_of_and_a_gauge_is_never_cut`.

## What would change it

| If | Then |
|---|---|
| The way to compare stands the first result off the first screen of a phone | It gives way, in the order [0035](0035-the-search-page-is-one-box-and-the-look-gives-way-to-the-answer.md) gives. What a result says does not |
| The founder wants one cobalt button in sight, as the look had it | `WAY_TO_COMPARE` in `apps/web/src/components/CompareTray/look.ts` is `plain`, and the way to the comparison is cream in the bar |
| The founder wants nothing over the first result of a wide screen | `INVITE_STANDS` in the same file is `under`, and what says that areas can be compared stands under the first result on every screen |
| The founder wants the way to compare as high as a main control on a phone | `ON_A_NARROW_RESULT_A_BUTTON_IS` in `apps/web/src/components/ResultList/look.ts` is `main`. The first result of a phone is then higher, and has less room under it on the first screen: [the design of the look](../design/look.md), section 4, has what was measured of both |
| A person reads one area of a comparison as the better, by where it stands or by how it is drawn | What says so is taken out, and the test that would have caught it is written first |
| The service comes to give a fit for each area of a comparison | It is a new decision whether a comparison shows it. Today an area says its fit only from the search that is open |
