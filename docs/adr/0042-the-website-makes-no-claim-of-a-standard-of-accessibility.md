# 0042. The website makes no claim of a standard of accessibility, and keeps what was built for a keyboard and a screen reader

Status: accepted, 2026-09-26. The founder asked for the two things it takes away, once they had walked the website a second time. That the website then claims no standard was decided for them, from what they asked, and is theirs to overturn: the last section says what follows if they do. It amends [0033](0033-the-website-looks-like-the-map-of-a-gentle-game.md), which held that a rabbit who always moves can be stopped, and [0040](0040-a-page-that-explains-leads-with-a-key-and-folds-its-working.md), which counted the statement of accessibility among the pages that explain.

## Context

- The website had a page at `/accessibility`, the statement of accessibility. The name board of every page led to it, and so did the foot. It began: "Burro aims to meet the Web Content Accessibility Guidelines, version 2.2, at level AA. It has not been audited, and some of it has not yet been tried with the tools people use, such as a screen reader." Under that it said what the website is built to do, what is checked automatically, where it is known to fall short, what has not been tested, and how to report a problem. Of the last it said that there was nowhere to send a report yet.
- The guidelines ask that whatever moves for more than five seconds beside what is read can be paused, stopped or hidden. On their first walk the founder asked for a rabbit who always moves. The website said that it aimed at the guidelines, so a button was built that stops him, which a keyboard reaches and a screen reader names ([0033](0033-the-website-looks-like-the-map-of-a-gentle-game.md), as amended that afternoon). A rabbit who cannot be stopped was weighed then, and put aside for that reason alone.
- As the website was rebuilt after that walk, the button was held to be among what a critique does not give up, with the promises of the product. It rested on what the website said of itself, and what the website says of itself is the founder's to say.
- The founder walked the website a second time, and wrote: "remove the pause button for the rabbit, for accessibility we will rely on users having motion turned off in the browser". And: "get rid of the accessibility tab. Overkill".
- With the button gone, a page that said the guidelines are aimed at would say what is no longer so of the first thing that moves on the first page. The statement was held to stay true: a test read it against the website, and the guide of the website said "Do not claim what has not been done."

## Decision

**The website says nothing of any standard of accessibility. The page that did is gone, and the button that was built to keep its word is gone. What was built so that a person can use the website with a keyboard, with a screen reader, or with less movement stays, and so does every test that holds it.**

| Taken away | What went with it |
|---|---|
| The statement of accessibility | The page at `/accessibility`, its words, its link in the name board and in the foot of every page, its place in what a search engine is told the website holds, and the way to it in `apps/web/src/lib/paths.ts`. The name board holds the name of the website and three links |
| The button that stops the rabbit | What it said to a screen reader, its row in the key to the drawings, and what the page kept in memory to know that he was stopped. Its drawings were among the drawings still, and nothing drew them. *They were taken away later that night, with the drawings of the rabbit as he asked* |
| The tests of both | A test of a thing that is gone goes with it. No test of what stays was taken out, loosened or marked to be skipped |

| Stays | What holds it, in `apps/web` |
|---|---|
| Every control is a native element, and the whole of a search, a comparison and a shared link can be made with a keyboard alone | `test_a_search_can_be_made_and_refined_by_keyboard_alone`, `test_a_search_can_be_shared_by_keyboard_alone`, `test_areas_can_be_chosen_and_the_comparison_reached_by_keyboard_alone` |
| The two tabs a search begins at are tabs to a keyboard and to a screen reader | `test_the_arrow_keys_move_between_the_tabs_and_go_round_at_either_end`, and the tests beside it |
| The focus is in sight, and is never left on nothing | `test_removing_a_chip_moves_the_focus_to_the_chip_beside_it_and_never_leaves_it_on_nothing`, and the tests of `test/access/` |
| What happens is said to a screen reader, once | `test_each_state_is_announced_once` |
| A drawing is dress, and what it stands for is said in words. The rabbit says nothing to a screen reader | `test_the_drawing_of_him_says_nothing_to_a_screen_reader_whatever_he_does` |
| Colour is never the only sign of anything | `test_rank_and_status_are_in_words_wherever_they_are_in_colour` |
| What is read has the contrast it needs, on cream | `test_every_colour_pair_has_the_contrast_it_needs`, `test_what_is_read_is_read_on_cream_and_never_on_the_grass` |
| Everything the map shows is in a table | `test_everything_the_map_shows_is_in_the_table` |
| Nothing needs to be dragged, and every control is one of two sizes | `test_every_slider_can_be_set_without_dragging`, `test_every_control_takes_a_target_size` |
| Nothing moves or changes size under a press, the pointer or the focus | `test_nothing_moves_or_changes_size_because_the_focus_or_the_pointer_came_or_went` |
| **Where the system asks for less movement, nothing moves**: the rabbit is still wherever he is drawn, no chip drops, and the words of a button stay where they are | `test_the_length_of_every_movement_is_a_token_which_is_nought_until_movement_is_welcome`, `test_nothing_moves_unless_the_system_says_motion_is_welcome`, `test_where_the_length_of_a_hop_is_nought_nothing_of_him_stirs_and_he_is_drawn_still` |
| The checks that a test cannot make are made by hand, in a browser | [The design of the website](../design/web.md), section 9 |

**What the design holds in the place of the statement.** [The design of the website](../design/web.md), section 9, is what the website is built to, point by point, with the test that holds each. It says of one point that it is not met: a person cannot pause, stop or hide the rabbit. At its foot it keeps the two lists that the statement held, brought to the website as it is: where it is known to fall short, and what nobody has tested. It is for whoever changes the code, and makes no claim to a visitor. What is the founder's to decide of it is in [the design of the look](../design/look.md), section 5. None of it is on any page.

What was weighed, and put aside:

| Way | Why not |
|---|---|
| The statement kept, with the rabbit named among where the website falls short | The founder asked for the page to go, and called it overkill |
| The statement kept, and its first sentence taken out | A page headed as a statement of accessibility is read as a claim, whatever its first sentence says |
| The button kept, and drawn smaller or further from him | The founder asked for it to go |
| The rabbit still at rest, so that nothing moves without end | The founder asked for a rabbit who always moves ([0033](0033-the-website-looks-like-the-map-of-a-gentle-game.md)). It is built, and one line chooses it |
| What stops him kept in the browser, so that a person says it once | The website keeps nothing in a browser ([0011](0011-nothing-is-kept-for-a-search.md)). It was so of the button too |

## Consequences

- **A person who is troubled by movement, and whose system does not ask for less, cannot stop the rabbit.** He moves beside what is read, from the moment a page opens and for as long as it is open. Such a person must find the setting of their system or of their browser, and no page tells them that there is one. The guidelines ask for a way to pause, stop or hide what moves so. Whether a setting of the system is such a way was not read, at the guidelines or anywhere else, so this record does not say that the guidelines are met there.
- **Where the system asks for less movement nothing is lost.** He was still there before, and the button was not drawn.
- **Nobody is told where the website falls short, or how to report a problem.** The statement said both, and said that there was nowhere to send a report yet. There is still nowhere. [The launch checklist](../legal/data-protection-checklist.md), task 11, asks for an address before launch, and a page to say it on is no longer built.
- **No law was read for this decision.** Whether a website such as Burro must publish a statement, and what the duty to make reasonable adjustments asks of one, were not read. They are the founder's to read before launch, with the rest of the checklist.
- **The tests hold what the website does, and no longer what a page says it does.** One test held the figures the statement named to the style sheets, and others held what it said of the rabbit and of the look to the website. Those tests went with the page. What they read of the website is still held by the tests of each part.
- **Every other record that named the statement is amended with this one**: [0033](0033-the-website-looks-like-the-map-of-a-gentle-game.md), [0035](0035-the-search-page-is-one-box-and-the-look-gives-way-to-the-answer.md) and [0040](0040-a-page-that-explains-leads-with-a-key-and-folds-its-working.md). Where one of them says that the statement says a thing as a shortfall, the design says it now.
- **The iPhone app is as it was.** It has no rabbit and no statement, and nothing of it was changed for this.

## What would change it

| If | Then |
|---|---|
| The founder wants the website to say that it aims at a standard | The statement is written again, from section 9 of the design and from what is known to fall short. Before it says so, either a way to stop the rabbit is built again, or he is still where he rests: `AT_REST` in `apps/web/src/components/kit/Burro/look.ts` |
| A person writes that the rabbit troubles them | He is stilled where he rests, in that one line, and read again with [the page on children](../legal/access-by-children.md) |
| A regulation, or a person who is qualified to say, holds that a statement is owed | It is written before launch, as above |
| Burro is given an address to write to | A page says it, by a name a person understands, and the foot of every page leads to it |
