# 0036. The box sends what was added, and what is kept to know it is counts

Status: accepted, 2026-09-26. It follows [0005](0005-raw-prompts-are-never-stored.md) and [0011](0011-nothing-is-kept-for-a-search.md), and changes neither. What a person is told, and the calls that were made in the building, are the founder's to overturn: the last section says which. It is of the website. The iPhone app has the fault this mends, and is not mended.

## Context

- The server keeps nothing for a search ([0011](0011-nothing-is-kept-for-a-search.md)). The client holds the search and sends it with every sentence.
- Once a search is open the box is labelled "Add to this search". It keeps what was typed, so that the words an offer rests on can be shown in it, and what is typed next is typed after them.
- The box sent all that it held. The service cannot tell words it has read from new ones, so it read the first sentence a second time, onto the search as it then stood.
- Seen in a browser. A person searched for a one bed up to £1,700 a month, leafy and quiet, 35 minutes from a place. They set the budget to £1,800, the journey to 30 minutes and Leafy to 80 by hand, typed a few words more after the sentence, and searched. The budget was £1,700 again, the journey 35 minutes and Leafy 100, and a vibe nobody had touched counted for 75 where it had counted for 50. Nothing said so.
- What a person types stays in the box it was typed in, and in the body of the `POST` that reads it ([0005](0005-raw-prompts-are-never-stored.md)). So nothing may hold the words as they were, to tell new from old by.

## Decision

**The box sends what stands in it after the words the search has read, as it was typed, and never those words a second time. What the search keeps to know how far it has read is counts, and no word.**

| Matter | What is so |
|---|---|
| What is sent | Until a search has read anything, all that the box holds. After that, what stands after the words that were read, with the search as it stands. It is cut where the search had read to and trimmed of space alone: it may begin with the comma it was typed after, and the service reads it as it reads a sentence that begins with none |
| When words are read | Once their answer is in and something came of them: an edit, taken or turned away, an offer or a question. Words that could not be sent, were refused, were stopped, or that nothing came of, are still to be read. Said another way where they stand, they are sent again |
| Where a model reads | It is asked of the same words, and of nothing before them |
| Nothing new in the box | Nothing is sent, and the box says why. It sent the sentence again, and a sentence sent twice made what it names count for more |
| A word changed among those that were read | It is not read again. The count moves with the words, so that what is added after them is still cut in the right place, and at the next Search the box says that a change to the words before what is added is not read |
| Words that were read and come back into the box | They are no addition. What the keys that undo and that do again put back is taken as read, and so is a copy of words of the box that is pasted into it |
| A change that cannot be placed | All that the box holds is taken as read, and as changed. No word is ever read twice, and the box says that words were not read |
| What is kept | Counts of the characters of the box, and whether a thing is so: how far the search has read, whether words before that place were changed since, where the words that were last read begin, how far it will have read once the words that are being read are answered and had read when they were sent, how many characters that were read were taken out, and what it knew of the box at the times the keys that undo and that do again lead back to, 64 of each at the most. They are held in memory while the tab is open, and mean nothing without the box |
| What is never kept | A word, a copy of one, a hash of one, or the length of one. The website never reads the clipboard: what was copied from the box is known by where it was taken from and how long it was |
| Where it is moved | `apps/web/src/lib/search/mark.ts`, and nowhere else. The box tells the store where it was changed, in counts, and never what was typed |
| Where words stand | The service counts from the start of what it was sent. The box hands the page those words, and selects among them counted from there, so "You wrote" and "Show in the box" fall on the words they are of, whatever stands before them |

Why counts, and no word. To say what was changed to what, the search would hold the words as they were: a copy of what was typed, outside the box. A hash of them would say only whether they are the same, and a hash of a short text is guessed by trying texts ([0005](0005-raw-prompts-are-never-stored.md)). A count says how much of the box was read, and says nothing to whoever does not hold the box.

What was weighed, and put aside:

| Way | Why not |
|---|---|
| Read the sentence again, onto the search as it stands | It is the fault |
| Take a changed box for a new search, and read all of it | A person who mends one letter loses everything they set by hand, with no way back |
| Keep the words as they were, or a hash of them | The reasons above |
| Have the service tell the words it has read from new ones | The server keeps nothing for a search |
| Take every word that was sent as read, whatever came of it | After "Nothing in that could be read" a person could not say it another way where it stands |
| Tidy what is sent: take off the comma, or "and" | What is typed goes as it was typed ([0023](0023-what-is-typed-goes-as-typed-and-people-are-told.md)) |
| Hold the box to the 600 characters the service takes, in all | The box would fill with what was read, and take no more |
| Read the clipboard, to know what is pasted | It may hold anything a person copied anywhere |

## Consequences

- **What was set by hand stands.** Seen on the fault itself, at both sizes: the second request held the 52 characters that were added and nothing of the first sentence, and the chips said £1,800 and 30 minutes after it.
- **A person who mends the sentence where it stands is not read, and is told so.** They type the change at the end, or use the settings. Words that were not read in the middle of a sentence cannot be put right where they stand: they are behind the place the search has read to.
- **Words that rest on what came before them are read by themselves.** "25 minutes max", "by bike" and "forget the budget", typed after a sentence, are each sent alone, and the rules read nothing of them. The box says that what was added was read by itself. They were not read before either: the sentence was offered again, thing by thing, over the search it had made.
- **An offer that was not chosen goes when the box changes, and does not come back.** It came back because the words it rested on were read again.
- **What the keys that undo put back may cost words that are new.** They say too little of what they did. So as many characters after what was read as were ever taken out of it are taken as read, and the box says so.
- **An attribute of the page holds a count.** The most the box takes is how far the search has read and the 600 together. No word is in any attribute.
- **It was seen in one browser.** Where the box was changed is worked out from where the caret stood, and what came back by what those keys leave selected, which was seen in Chrome alone. No word that was read is sent again by any way that was tried. In a browser that leaves no more than a caret after the keys that undo, words may go unread with nothing said. Autocorrect, dictation and a keyboard that composes characters were not tried.
- **The iPhone app sends the text it is handed**, with the search as it stands, and has no count.
- What holds it: `test/search/added.test.tsx`, which answers a request only if it is one the service was sent when the walk was recorded, `src/lib/search/mark.test.ts`, and `test_it_is_kept_as_counts_in_the_store_and_no_word_of_the_box_is_kept_anywhere`, which plants a word in a sentence and in what is added, and looks for it in every state of the store, in storage, the console, every address and every attribute.

## What would change it

| If | Then |
|---|---|
| The reader comes to read words that refer back, given the search they are added to | Nothing here changes: they are sent as they are, with the search |
| The founder wants a change among words that were read to be read | More than one place is kept: where each stretch that was read begins and ends. It is still counts |
| The founder wants no count in the markup | The box is held to 600 characters in all, and a person empties it to type more |
| The founder wants "Take it all back" to keep what was set by hand since the press | It puts back the search as it stood before the press, as designed. To keep what was set since, the edits made since are sent again after it |
| A browser is found whose keys that undo say less, or lead elsewhere | The box says that words were not read wherever it cannot place what came back, as it does for a change it cannot place |
| Accounts, and a search that is kept for a person who is signed in | [0011](0011-nothing-is-kept-for-a-search.md) says what changes then. What is typed is still kept nowhere |
