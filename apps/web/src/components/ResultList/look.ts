/**
 * Calls of the look of a result, each built more ways than one and each chosen in one line
 * here. None changes what a result says of its area, in which order, or what a press does.
 *
 * They are plain values in a file of their own, kept apart from the list, which runs in
 * the browser.
 */

/**
 * How large the town of a result is drawn, on a result that has room for one. `ground`:
 * at the pixel of the ground, two pixels of the screen to one of its own on every screen,
 * so that it is 112 by 64 and about as high as the name and the fit it stands beside.
 * `screen`: at the art pixel of the screen, as every other drawing is, which is 168 by 96
 * on a wide screen and half as high again as what it stands beside. It asks for a wider
 * result, so that a name keeps its room: one of 39rem, where the smaller asks for 36rem.
 */
export type TownDrawn = "ground" | "screen";

/** This is the one line that chooses. */
export const TOWN_DRAWN: TownDrawn = "ground";

/**
 * Where the line stands that says what a town is, and that it is no picture of the place.
 * `none`: on no result. The founder, who had walked the website twice, asked for it to go
 * from the results: what a town is, is said in the key to the drawings and at the head of
 * the page of an area. `once`: once, of every town of the list, and under no town as that
 * town's own: over the list, or with the first town of it, as `OVER_THE_LIST` chooses.
 * `each`: under every town, in the words of the town itself, and nowhere of them all.
 */
export type LineStands = "none" | "once" | "each";

export const LINE_STANDS_AT: readonly LineStands[] = ["none", "once", "each"];

/** This is the one line that chooses. */
export const LINE_STANDS: LineStands = "none";

/**
 * What stands over a list of results whose results have room for a town, between what
 * refines the search and the first result. One thing is said once of a list: that areas
 * can be compared. Where `LINE_STANDS` has the line of the towns stand once, that is a
 * second.
 *
 * `slip`: in one slip of cream over the list. Measured at 1440 by 900 beside the map as
 * wide as it now is, with both in it, the slip was four lines and 92 px high, and the
 * first result stood 100 px lower for it. `nothing`: nothing. That areas can be compared
 * is said by the page that draws the list, beside what refines the search and on its
 * line, and a line of the towns stands under the heading of the first result, where the
 * first town is. Neither stands between the search and the answer.
 *
 * On a result with no room for a town nothing stands over the list whichever is chosen.
 */
export type OverTheList = "slip" | "nothing";

export const OVER_THE_LIST_MAY_STAND: readonly OverTheList[] = ["slip", "nothing"];

/** This is the one line that chooses. */
export const OVER_THE_LIST: OverTheList = "nothing";

/**
 * What becomes of a town on a result with no room for one beside its name and its fit, as
 * every result of a phone is: one under 36rem wide. A wider result is laid out as it is
 * whichever is chosen. `none`: no town is drawn there, and no line over the list, so that
 * a name keeps its room and the first result is whole on the first screen of a phone.
 * `beside`: the town is drawn at the far end of the heading all the same. The name, the
 * fit and what stands beside the name then have a line each, and the heading of a result
 * of a phone is 46 px higher. Beside a town a name has 146 px on a phone 360 px wide, and
 * less on a narrower one: a name of one word of twelve letters is broken inside the word.
 */
export type OnANarrowResult = "none" | "beside";

/** This is the one line that chooses. */
export const ON_A_NARROW_RESULT: OnANarrowResult = "none";

/**
 * How the two ends of a gauge are drawn on a result. `pictured`: each by its one small
 * picture, and nothing under it. The founder, who had walked the website three times,
 * asked for a picture at each end of every gauge and for fewer words: what an end is
 * called is said by the name of the gauge, to whoever hears the page, and in the working
 * of the result. `named`: each by its picture with the name of its end under it, as the
 * service names the end, and the end that was asked for named heavier. A line is then a
 * line of words higher.
 *
 * Either way each end of every gauge has one picture, at every width, and the steps of
 * every line of every result stand in one column.
 */
export type EndsOnAResult = "pictured" | "named";

export const ENDS_ON_A_RESULT_MAY_BE: readonly EndsOnAResult[] = ["pictured", "named"];

/** This is the one line that chooses. */
export const ENDS_ON_A_RESULT: EndsOnAResult = "pictured";

/**
 * How the trade-off of a result is drawn. It stands out by where it stands and how it is
 * drawn, and never by red, which says danger, nor by anything that says the area is the
 * worse for it: a trade-off is what was given for what was got.
 *
 * `band`: on a band of sand of its own, from edge to edge of the result, over the two
 * ways on. Its heading stands on a plate of ink, with a pair of scales beside it whose
 * pans hang level. `box`: in a box of its own within the result, in an edge of ink with
 * the hard shadow of the look, its heading in ink with two arrows beside it, one each way.
 *
 * Either way it keeps its sentence, word for word, and the key of its source is in the
 * working of the result.
 */
export type TradeOffDrawn = "band" | "box";

export const TRADE_OFF_MAY_BE_DRAWN: readonly TradeOffDrawn[] = ["band", "box"];

/** This is the one line that chooses, for a result and for the key to the drawings. */
export const TRADE_OFF_DRAWN: TradeOffDrawn = "band";

/**
 * What stands beside the word of a trade-off, each way one is drawn: a pair of scales
 * whose pans hang level, on the band, and two arrows, one each way, in the box. A result
 * draws it by this and the key to the drawings shows it by this, so that the key shows the
 * drawing a result draws whichever way the line above chooses.
 */
export type BesideATradeOff = "scales" | "arrows";

export const BESIDE_A_TRADE_OFF: Readonly<Record<TradeOffDrawn, BesideATradeOff>> = { band: "scales", box: "arrows" };

/** The drawing of each, by its name among the drawings. */
export const DRAWING_OF_A_TRADE_OFF = { scales: "ui-tradeoff", arrows: "ui-tradeoff-b" } as const;

/**
 * Where the vibes stand that nobody asked for, of which the service gives two at the most
 * with every result: those the area sits at an end of. `alone`: on a result only where no
 * vibe was asked for, so that a result is never without a gauge, as a phone drew them. A
 * result then holds a line for each thing that was asked for and no other. `beside`:
 * under what was asked for as well, each run under a word that says which it is, as a
 * desk drew them. `never`: on no result, so that a result holds what was asked for and
 * nothing else, and no gauge at all where no vibe was asked for.
 *
 * Whichever it is, every one of them is in the working of the result, with its source,
 * and on the page of the area.
 */
export type OthersStand = "alone" | "beside" | "never";

export const OTHERS_MAY_STAND: readonly OthersStand[] = ["alone", "beside", "never"];

/** This is the one line that chooses. */
export const OTHERS_STAND: OthersStand = "alone";

/**
 * Where what a fit is based on is said, where that is not everything that counts. `working`:
 * on the result two words say that the fit is not whole, after the mark of what is not
 * whole, and each thing that was asked for and has no figure has a line that says so. What
 * the fit is based on, what it leaves out, and each firm limit that could not be held
 * against the area are said in full in the working, one press away. `result`: in full on
 * the result, under its fit, as it was: a sentence for each, heavier where it is of what a
 * person asked for.
 *
 * Either way a fit is never given alone where it is not whole, and what is not known is
 * said to be not known, in sight, with nothing pressed.
 */
export type FitSaid = "working" | "result";

export const FIT_MAY_BE_SAID: readonly FitSaid[] = ["working", "result"];

/** This is the one line that chooses. */
export const WHAT_A_FIT_IS_BASED_ON_IS_SAID_IN_THE: FitSaid = "working";

/**
 * How high the buttons of a narrow result are, as every result of a phone is: the way to
 * compare in its heading, and the two ways on at its foot. `small`: as high as a small
 * button of the look, 34 px, so that the way to compare costs the first result of a phone
 * no height and the first result is whole on the first screen, with 16 px under it.
 * `main`: as high as a main control, 44 px. The first result of a phone is then 15 px
 * higher, and whole on the first screen with 2 px under it.
 */
export type OnANarrowResultAButtonIs = "small" | "main";

/** This is the one line that chooses. */
export const ON_A_NARROW_RESULT_A_BUTTON_IS: OnANarrowResultAButtonIs = "small";
