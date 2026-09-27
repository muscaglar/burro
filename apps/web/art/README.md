# The drawings

Every picture of the website is drawn here, as text, one character a pixel. Nothing in `public/art/` is drawn by hand.

```
npm run gen:art      make public/art/NAME.png of every drawing, and src/lib/art/names.ts
npm run check:art    fail, and say which, if a picture or the list is not what the drawings give
```

Both are `scripts/gen-art.mjs`. `npm run check` runs the second. The same drawings give the same bytes on every machine, so a picture is committed beside its drawing, and a check that fails on another machine has found a drawing that was changed and not made again.

## A file of drawings

A file is `NAME.sprite.txt`. It holds a palette and as many drawings as belong together. The name of the file is for whoever reads the folder: a picture is named for its drawing.

```
# a note
palette
. transparent
k #2a2140
s #e9cf94

== dot
# 3 x 3. A note on what it is. A line that begins "# " is no row of the drawing.
.k.
ksk
.k.
```

Rows of one drawing are of one width. A name is lower case, digits and hyphens, and is drawn once. The format holds nothing that a text editor cannot show, so that a drawing is read, changed and reviewed as any other line of the repository is.

A drawing may say three things of itself, before its first row. Each goes into `names.ts`, where a part reads it.

| Line | Says | In the list |
|---|---|---|
| `# @cut 12` or `# @cut 9 3 6 12` | Where a frame is cut in nine, written as `border-image-slice` is | `cut: [top, right, foot, left]` |
| `# @frames 8` | How many drawings of one width stand side by side in a strip | `frames: 8` |
| `# @face 2 7 17 9` | Where a figure is set on it in type: from the left, from the top, how wide, how high | `face: [left, top, width, height]` |

## Town Map

The look is Town Map's: the map of a gentle game. Its drawings are taken as it drew them, under its names, and what it did not draw is drawn in its manner: an outline of ink one pixel wide, flat colour, a light pixel where the light falls and a shade down the right and along the foot. Two things of Town Map are not taken: the donkey, and the city drawn as little towns on a grid.

One thing is changed in what is taken. Town Map held its brown in wood and in leather, and as the shade of amber and of poppy. Brown is the rabbit's and his burrow's, and nothing else on the website holds it. So where a drawing of Town Map's held brown it holds another colour: poppy under amber, shade under poppy and for wood, and a colour of its own for a boot and a purse. Each drawing says in its own line what was turned.

## Burro

Burro is a rabbit: a wild one, brown and grey, with a pale belly and a pale scut. The name is a play on a London borough, and on the burrow a rabbit digs to make its home. Five drawings are named for him: three of him, a strip of the soil that flies as he hops, and a strip of what he does where he rests. There is no other: he asks nothing and nothing stops him, so nothing is drawn of him asking, and no button of his.

| Drawing | Is | Where |
|---|---|---|
| `burro-sits` | He sits, seen from the side, at rest | Beside the heading of the first screen, before a search. In the name board of every page and, on a narrow screen, over the foot of every page, where he is seen from his back up |
| `burro-hops` | He hops in and out of his hole: a strip of twelve frames | Centre stage, where the results are about to stand, while a search is read |
| `burro-hops-soil` | The soil that flicks up from his hole as he comes up, and again as he goes down: a strip of twelve frames, one for each frame of his hop. In six of them nothing is drawn | The same place, laid over his hop |
| `burro-waits` | He sits up beside his hole, still | The same place, for a person whose system asks for less movement |
| `burro-sits-stirs` | What he does where he rests, which is where he sits: a strip of fifteen frames. His body with what moves taken out, then his ears, his eye and his nose, each a part of him alone, and then what he does now and then, which is the whole of him | Wherever he sits, laid over him in layers, each on a clock of its own |

He is drawn by what every page stands in, so that he is on every page: in the name board where it has room for him, and over the foot where it has not. Where the page itself draws him, beside the heading or where he hops, he is drawn nowhere else: he is one rabbit. He is on no result, not on the map, and beside no failure.

Every drawing is on a canvas 24 wide and 30 high, and a frame of the strip is one canvas. He stands on row 28, counted from nought, and so does his burrow: so he never jumps as one drawing gives way to the next.

The hop, frame by frame: the hole alone; his ears come up; his head and his forepaws; he climbs out; he springs out; he is out, and sits up; he looks about; he turns; he goes down head first; his haunch and his scut; his scut, last; the hole alone. The last frame is the first, so the strip comes round with no jump and the hole is alone for a beat. His hole is in one place in every frame. `burro-waits` is the frame in which he is out and sits up, point for point, so the box he is drawn in holds the same picture whether he moves or not.

He is shown large where he hops, each art pixel five pixels of the screen, so every frame is a drawing of him that stands by itself. The strip is shown a frame at a time, in steps: a frame is never slid into view.

Nothing on a page stops him. Where the system of a person asks for less movement he is drawn still, in the drawing of his pose, and that is the one thing that stills him.

He wears nothing, holds nothing and has no smile, and his eye is two pixels. His fur is `fur`, lit in `sand` and shaded in `shade`. What is pale of him is `page`: his belly, his muzzle and his scut. His outline and his eye are `ink`. His burrow is `earth`, its clods are `shade`, and the dark of its mouth is `ink`. The soil he throws up is `earth` and `shade` too, and has no outline. The light is from the top left in every frame, whichever way he faces.

## What a drawing is held to

- **The colours of the look and no other.** They are the seventeen that `src/styles/tokens.css` names, by the same names, in one list at the head of `scripts/gen-art.mjs`: `ink`, `page`, `lea`, `sand`, `meadow`, `verge`, `hedge`, `shallows`, `haven`, `cobalt`, `amber`, `poppy`, `heath`, `fur`, `shade`, `slate` and `earth`. Three more may come to stand beside them. A colour is added to the style sheet and to the foot of the list in one change, and `test/art.test.ts` fails where the two differ. A pixel is one of them, whole, or it is clear. Nothing is see-through. The command refuses any other colour, and names the drawing.
- **One light, from the top left.** An outline of ink, one pixel. The light edge is at the top and the left, the shade at the foot and the right.
- **96 art pixels at the most, each way.** A strip is held by its frame. The ground alone is set apart, by name: it lies behind everything, and is large so that its repeat does not show.
- **No word and no figure in a picture.** A picture cannot know which city a release is of, or how long a journey may be. What a drawing says is set on it in type, from what the service sent.
- **Nothing that pictures a person.** A vibe of the family `who_lives_there` is a page of a register, ruled, with a band at its head, and nothing else. At the two ends of its gauge it is that page, with one line written on it and with every line. A swing has nobody on it.
- **Neither end of a gauge is the better one.** A picture at an end says what there is, and never that it is good or bad: no tick and no cross, no smile and no frown, and no red for the one and green for the other. Each end has one picture, and the two are opposites: what each end is, of a vibe that runs between two ends that have names, and little of the thing and much of it, of a vibe that runs one way.
- **Recorded crime is a count that was written down.** It is drawn as a sheet on its board with a tally on it, stroke by stroke. It is never a warning, a mask, a weapon, a broken thing or a light that flashes, and nothing of it is poppy. Nor is anything poppy at the end of a gauge where more crime was recorded. Red says danger, and no place is given a verdict.
- **No name and no mark of a company.** The brands nearby are a carrier bag with nothing on it.
- **No line in pieces.** No edge, rule or line of a drawing is drawn in dots or in dashes: a person who walked the website did not know what an edge in pieces was for. What marks a blank is one whole line of shade. What is left in dots is a thing that is drawn, and is written down with what it is: the tines of a fork, the eyelets of a boot, the windows of a block. `src/components/kit/drawings.test.ts` reads every drawing for a line of dots, and `src/components/Town/marks.test.ts` holds what marks a blank in a town.
- **Brown is the rabbit's.** No drawing but his holds `fur` or `earth`.
- **A press lands where it was aimed.** A button pressed is drawn on the canvas of the button up, with its cut: only its face steps, one art pixel down and one to the right, into the place of its shadow. The button itself never moves and never changes size.
- **Nothing of a donkey.** The look was first drawn round one, by a wrong guess at the name, and all that was his is gone: his panniers, his stable and its yard, the lamp, the skyline, the load he carried. `test/art.test.ts` refuses a drawing that is named for any of it.

## How they are named

| Name | Is |
|---|---|
| `ground` | The ground of every page: the meadow, in tiles. 192 square |
| `tile-grass-a`, `-b`, `-c`, `-d` | The four tiles of meadow the ground is made of: three tufts, two daisies, one tuft, and plain. They are the grain of land, for the map |
| `tile-water-1`, `tile-water-2` | The grain of water, for the map |
| `ui-box`, `ui-box-on` | The box, which is the one frame of the look, and the box that is chosen or in hand. Cut in nine. `frame-box` and `frame-box-on` are the same two, under the names the tokens `--frame-box` and `--frame-box-on` give them |
| `ui-button`, `ui-button-go`, `ui-button-on`, `ui-button-stop` | A button, cut in nine: plain in page, the one that matters most in cobalt, what is on in amber, what stops in page with an edge of poppy |
| `NAME-down` | The button `NAME`, pressed |
| `ui-carrot`, `ui-key`, `ui-peg`, `ui-cross`, `ui-arrow`, `ui-weight` | The pointer of a menu, the key of a source, the peg of a band, the cross that takes a chip off, an arrow, the mark of how much a thing counts |
| `ui-tradeoff`, `ui-tradeoff-b` | What stands for a trade-off, which says that one thing was given for another, drawn two ways so that a result may show either: a pair of scales whose pans hang level, and two arrows, one each way. Each is 16 square, and neither holds any poppy |
| `ui-approx` | The mark of what is not whole: one step of a band, chequered in squares two art pixels wide, as the step is that a peg stands on where a band rests on part of what it needs. 9 by 6, as a step is |
| `thing-ID` | A thing of a search, which stands beside the words of a chip: by the id the service gives, with every underscore a hyphen. `thing-leafy` for the vibe `leafy` |
| `thing-vibe-ID` | The thing of a vibe whose id would give it the name of another thing: `thing-vibe-family-amenities` for the vibe `family_amenities`, which would be named as the thing of a family is. No vibe is drawn by the thing of a family, so under that name its drawing was drawn nowhere |
| `thing-family-ID` | What stands for a vibe or a measure that has no drawing of its own, by its family. And what stands for a group of measures that the settings show apart from the families of vibes, by the dimension the service gives its measures: `thing-family-brands`, `thing-family-air-noise` and `thing-family-crime` |
| `thing-plain` | What stands for whatever has no family that is drawn |
| `thing-NAME-off` | The thing `thing-NAME` in outline, its colour taken off it: what is drawn for a thing that counts for nothing |
| `thing-journey`, `thing-budget`, `thing-tenure`, `thing-home`, `thing-area`, `thing-alike`, `thing-usual` | The things that are no vibe: a journey to a place, what can be paid, renting or buying, the kind of home, an area that was named, more like a place, and the usual settings |
| `end-ID-low`, `end-ID-high` | The picture at each end of the gauge of a vibe, by the id the service gives the vibe, with every underscore a hyphen: `end-leafy-low` and `end-leafy-high` for the vibe `leafy`. One picture at each end. Each is 16 square, as a thing is, and stands on its last row |
| `end-ID-low-b`, `end-ID-high-b` | The same end, drawn a second way, where it was not plain which picture says the end best: a lamp over a bare street where little is green, a bench alone where few parks are close by, and a bench under a tree where they are. `WAY_OF_ENDS` in `src/components/kit/Ends/look.ts` chooses which way is drawn, in one line, and an end that was drawn one way is drawn that way whichever is chosen |
| `end-blank` | What stands at both ends of the gauge of a vibe that has no pictures of its own: a plot marked out by one whole line, low and wide. 16 square |
| `key-END` | The picture at an end of a scale, for a part that knows the end by the words the service gives it, in lower case: `key-calm` and `key-buzzy`. Each is the picture of that end of its vibe, `end-ID-low` or `end-ID-high`, set in the middle of a canvas of 32 by 22 and on its last row. `key-least` and `key-most` are the two ends of what runs one way, where it is drawn by no vibe of its own. `key-blank` stands where such an end has no picture of its own, and beside the heading of the page that is not there: a plot marked out by one whole line, and a house not yet given a roof. It is kept as two, for that page: the plot alone is `end-blank` |
| `gauge-cell`, `gauge-cell-full` | One step of a gauge, empty and filled |
| `btn-less`, `btn-more`, and each with `-down` | The two buttons of a step, and each pressed. Shown whole, 22 square |
| `ui-flag` | The pennant of a rank: a flag of page on its pole, the same for every rank |
| `pin` | The pin of the map: a head of page, and a point under it |
| `burro-POSE` | Burro. `burro-hops` is frames side by side |
| `burro-POSE-stirs` | What he does where he rests in that pose: frames side by side |
| `burro-POSE-soil` | The soil that flies as he hops: frames side by side, one for each frame of his hop |
| `town-plot` | The plot a town stands on: a sod of meadow, seen from a little above. 56 by 32 |
| `town-low`, `town-mid`, `town-tall` | A house, a terrace and a block: a wall and no roof, 14 wide and 7, 11 and 17 high. Each is a strip of 4, 6 and 10 frames: its windows not known, then none lit, then one more lit in each |
| `town-roofs` | A roof, which stands on any wall. A strip of 5 frames, each 14 by 6: no roof, where the wall is closed by one whole line of shade, two newer in slate, two older in poppy |
| `town-trees` | What stands in front of the buildings. A strip of 3 frames, each 13 by 11: where a tree would stand, marked by one whole ring of shade, and two trees |
| `town-lot` | Where a building would stand, marked out on the meadow by one whole line of shade and not built on. 9 by 5 |

## The ground

Town Map laid a ground of 64 art pixels, four tiles by four. Across a desk it came round eleven times, and the eye found its daisy every time. The ground here is 192 art pixels, twelve tiles by twelve, and is laid at 2 px to the art pixel: it comes round under four times across a desk of 1440 px.

It is set out so that it is a meadow and not a pattern. 118 of its 144 tiles are plain grass. Six hold daisies, and no two of those stand in one row of tiles, in one column or on one slant. No tile with anything on it stands beside another, or corner to corner with one. All of it is held round the edges too, where the ground lies against itself. `ground.sprite.txt` has the plan of it, a letter a tile, and `test/art.test.ts` reads the picture back into its tiles and holds it to each of these.

## What stands on what

| To draw | Put |
|---|---|
| The ground of a page | `ground`, laid again and again from edge to edge, each art pixel 2 px whatever the screen: the picture is then 384 px square. It lies against itself with no seam. Under it, where it has not come yet, `meadow` |
| A box | `ui-box` as a border image, cut `4 6 6 4` and filled, each side as wide as its cut times `--px`. Its shadow is in the picture, at the right and the foot, and `--box-shadow` lies under the picture in the same place: so a box has its shadow while its picture is on its way, and without it. A style sheet adds no other |
| A button | `ui-button` or another of the four as a border image, cut `3 3 4 3` and filled. Pressed, the picture alone changes, to the one named `-down`: the cut and the widths stay, so nothing moves but the face. Its words may step with it, one art pixel down and one to the right. What is stretched of a frame is one colour the way it is stretched, so a button up has its glint in its corner and a button pressed has none |
| Words on a button | Page on cobalt. Ink on page and on amber |
| A thing of a search | `thing-ID` for a vibe, or `thing-vibe-ID` where that name is another thing's, then `thing-family-ID` by its family, then `thing-plain`. The drawing is dress: the name beside it is the service's |
| A thing that counts for nothing | The drawing of the thing with `-off` after its name, in the place of the thing. Nothing is dimmed, and the words beside it say that it does not count |
| Where an area sits on a vibe | Five cells in a row, which the style sheet draws: Town Map's are 9 art pixels by 6, page with an edge of ink, one art pixel apart, and the one where the area sits is ink. `ui-peg` stands over that one, its point in the cell. At its low end `end-ID-low` and at its high end `end-ID-high`, by the id of the vibe: `picturesAtEnds` in `src/components/kit/Ends/picture.ts` chooses them, and the blank one at both ends where the vibe has none |
| What rests on part of what it needs | `ui-approx`, shown whole, before the two words that say so. The step the peg stands on is chequered as the mark is |
| A trade-off | `ui-tradeoff`, shown whole, beside the word. `ui-tradeoff-b` is the second way, of the same size |
| A group of the settings | The drawing of its family, `thing-family-ID`. A group of measures that stands apart from the families of vibes is drawn as a family is, by the dimension of its measures |
| A source | `ui-key` before the word, which opens in place |
| The choice in hand, of a menu | `ui-carrot` at its left, pointing at it |
| How much a thing counts | A row of `gauge-cell`, as many as there are steps, each lying one art pixel over the one before it, so that two steps share one outline: and `gauge-cell-full` in the place of each, from the left, as it counts for more. A step filled is drawn where the step empty was. Ten steps are 51 art pixels wide and twenty are 101. It is never the band of five: a cell of the band is wider than it is tall, none fills, and a peg stands over one |
| Burro, while a search is read | `burro-hops` in a box 24 by 30 art pixels, each art pixel `--px-stage`, which is 5 px: the strip is moved a frame at a time, in as many steps as `frames` says, over `--motion-hop`. `burro-hops-soil` lies over it in the same box, and is moved by what moves it. Where that is `0ms`, `burro-waits` in the same box, and no soil |
| The rank of a result | `ui-flag`, shown whole, and the number set on its `face` in type, in ink: in the reading face, heavy, since a number is read. It is sized as the drawing is. Two figures are 9 art pixels high, which is as high as the face lets them be, and three are 6, so that they stay on the face |
| The town of an area | `town-plot`, and on it what `src/lib/town/pieces.ts` lays. No other file lays a piece |
| A result on the map | `pin`, shown whole, and the number set on its `face` in type, in ink. Its point is the middle of its last row: it is set on the map by the middle of its foot |
