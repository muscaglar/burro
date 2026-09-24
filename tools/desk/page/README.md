# The page of the review desk

The one page a reviewer works in. Plain HTML, CSS and JavaScript, with no build step, no package and no file from any other machine. The design is [docs/design/desk.md](../../../docs/design/desk.md), section 5.

## The keys

They are the same in every queue. `?` shows them on the page.

| Key | Does |
|---|---|
| `1-9` | Give the answer with that number. It is saved, and the next item is shown. |
| `7` | Ratings: say that you do not know the area. Every vibe of it that is open is answered, and one undo takes them all back. |
| `Enter` | Give the answer marked as proposed, where one is. |
| `s` | Skip. The item comes back after the rest. |
| `u` | Undo. Takes back what the last key saved in this queue, and shows its item. |
| `n` | Write a note for the next answer. Enter keeps it. Esc leaves it. |
| `f` | Ask a second reviewer to look at the next answer, or skip. |
| `[  ]` | Look at the item before or after. Nothing is decided, and a note that was kept stays. |
| `Left, Right` | The same, where no map is shown. |
| `j` | Go to the next flagged item that is not done. Nothing is decided. |
| `o` | Rules: open the first of the items a rule shows. [ and ] go through them, and o comes back to the rule. |
| `g` | Choose a group, such as a borough. |
| `q` | List the queues. |
| `p` | Pause. The clock stops. Press p again to go on. |
| `?` | Show these keys. |
| `.  ,` | Read on in what is known of the item, and go back. Page Down and Page Up do the same. |
| `+  -  0` | Map: zoom in, zoom out, fit the item. |
| `An arrow` | Map: move it. With Shift, by a small step. A mouse can drag it, and its wheel zooms. |
| `a-e` | Names: choose a spelling. |
| `m` | Map: does to the cell under the cross what a click does. |
| `Click, click` | Borders: take up a cell, then click a cell of the area it should join. |
| `Click` | Names: say which area this is a name of. Click again to take it back. |
| `Esc` | Let go of a cell, leave a note, close a list, or drop a note that was kept. |

Every key but the map's and `o` also has a button, on the bottom line or beside the question.

## What to know before a long sitting

- An answer is on disk before the next item is shown. If the desk cannot write, the page says why, keeps the answer, and sends it again until the desk takes it. Do not close the page while it says so. The browser will ask before it lets you.
- The page says what was saved, on the line under the top line: "Saved: Right, with a note, for Tallowgate." If that is not what you meant, `u` takes it back, and gives its note back too.
- What is known of an item may be longer than its box. The page then says "More below": `.` reads on and `,` goes back. The words go when the last line is in view.
- The rule of a queue is open on its first item, and shut from the next. Click "The rule" to read it again.
- One answer is marked "proposed". `Enter` gives it, whichever number it is on.
- On a name proposed as another name there is no key `1`: the desk cannot make an area of another name. The other answers keep their keys. If the name should be an area, write a note and skip it.
- A name with a line "Look hard" is flagged, so `j` stops at it.
- Rules come first. Each is read in the middle of the page: the rule, how many items it would settle, what could go wrong, and ten of the items drawn at random. `.` and `,` page it. `1` adopts the rule: every item it fits that you have not answered is settled, and the line under the top line says how many. `2` changes nothing. `u` takes either back, and with a yes everything it settled.
- `o` opens the first of the ten items a rule shows, as it is shown in its own queue, with its map. `]` and `[` go through the ten, and `o` comes back to the rule. Nothing is decided while one is looked at: a key that would answer says so. The line under the top line says which of the ten is shown. A rule names the table of the draft that lists every item it would settle.
- A rule that leans on others settles a name only where the rule the name leans on is adopted too. Its screen says which of them are adopted, and what a yes would settle as they stand. It settles nothing while none is.
- An item that a rule settled says which rule. Your own answer takes its place. `u` in Names or Borders never takes back what a rule settled.
- The desk cannot take the ground from under an area. On a name of an area with ground, a line over the answers says that to turn the name down waits for a new draft, and each such answer is marked "(waits)". The answer is saved. Read every name first, then make the draft again from the answers, then look at borders. Borders and Whole boroughs say how many names wait.
- `j` goes to the next flagged item that is not done. In Borders the flagged borders of a borough come first, so `j` at the end of them goes to the next borough.
- `wrong` needs a note, and so does any answer on an area after you moved a cell of it. The page opens the note and waits. Enter sends the answer. Esc takes it back.
- After you move a cell the question is "With your moves, is it right now?". "Right now" says the border is checked. "Still wrong" keeps your moves, and lists the area for you to look at again.
- A move is saved the moment the cell is put down. `u` takes it back.
- "Another name", "a smaller place inside" and "a wider name" need the area named. If the item names none, the page asks for one: click a cell of the area, or move the cross over it and press `m`. Five areas at most.
- To write a note, press `n` first. Words typed with the note shut are taken as no key: the page says so, and does nothing. That is why a letter acts a third of a second after it is struck. A number and `Enter` act at once. Words typed slowly, a letter every half second, are still keys.
- A note that was kept, and a mark, go with the next answer you give. They stay while you look at other items. Esc drops them.
- A key struck in the first quarter of a second of a new item is dropped, so a key struck twice does not answer an item you have not read.
- In Ratings, `7` says that you do not know the area, for every vibe of it at once. It is beside `6`. One `u` takes all of it back, until the page is loaded again: after that `u` takes back one vibe at a time.
- If the page says "You answered this already", another tab is open on the same desk. Your answer there stands. Press the key again to change it.
- The clock counts only while the tab is in view and the page is not paused. No item counts for more than 15 minutes.
- After you move a cell the heavy outline is the border as it now stands, and the thin broken line is the draft.
- On a border, a mark on a cell says by its look what the doubt is: a ring for a margin under 10%, a square for a cell outside the main borough, a square on its point for a cell beside an area whose seed is close, a triangle for a cell cut off from the rest. A heavy dotted line is a stretch that follows no line. Two rings are the seed that stands close. The top left corner of the map says which looks are on it.
- A cell in doubt shows its code once the cross is on it, or once the map is twice as close: `+` twice. The lines of what is known are labelled with the same codes.
- The top line says which data is shown. If it does not say, decide nothing.

## The files

| File | Holds |
|---|---|
| `index.html` | The parts of the screen, empty. No script and no style is written in it |
| `desk.css` | Every colour and size. It follows the system's light or dark |
| `logic.mjs` | What the page decides: what a key means, what is sent, what is shown and said. Plain functions |
| `map.mjs` | Which layers may be drawn, where a point falls on the canvas, and what is drawn. Plain functions |
| `desk.mjs` | The page itself: it asks the desk, and copies what `logic.mjs` says to the screen |
| `test/` | The tests, and stand-ins for the desk and for the browser |

## To test it

```
node --test tools/desk/page/test/*.test.mjs
```

`make desk-check` runs it after the desk's own tests. It needs Node 20 or later and nothing else. The tests run the whole page against a stand-in for the desk and a stand-in for the browser, which is read from `index.html`. One of the desk's own tests, `tests/test_page_at_the_desk.py`, runs the page against the desk itself: `test/support/at-the-desk.mjs` is what it runs. No test opens a browser, so none says how the page looks, how a screen reader says it, or how fast a borough draws. Those are for a person to check, at the desk.

## What the page will not do

- Ask any machine but the desk for anything. Every address is a path, built in `logic.mjs`.
- Draw a basemap, tiles, or any layer but the nine of the design. A layer that names no source, or a source that may not stand behind a border, is left out, and the line under the map says which and why. That is a tripwire. The gate is the licence registry, which the step that fills the queues asks.
- Write a word from a file as markup. It is written as text.
- Keep anything in the browser. What was decided is on disk, with the desk.
