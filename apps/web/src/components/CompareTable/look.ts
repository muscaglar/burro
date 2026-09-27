/**
 * What is a matter of taste in how a comparison is drawn, in one line. It is plain code
 * with no state, kept apart from the parts that draw it, which run in the browser.
 */

/**
 * What the heads of the areas say of their towns, where the page hands over what a town is
 * drawn from. `nothing`: nothing. The founder, who had walked the website twice, asked for
 * the line that says what a town is to go from the results. It stood at the head of a
 * comparison in the same words, of the same towns, which a person comes to from the
 * results: so it goes from here as well. What a town is, is said in the key to the
 * drawings and at the head of the page of an area. `line`: once, in sight, before the
 * first of the towns, as it was. On a wide screen it then stands over the names of the
 * rows of the tables.
 */
export type HeadsSayOfTheirTowns = "nothing" | "line";

export const HEADS_MAY_SAY_OF_THEIR_TOWNS: readonly HeadsSayOfTheirTowns[] = ["nothing", "line"];

/** This is the one line that chooses. */
export const HEADS_SAY_OF_THEIR_TOWNS: HeadsSayOfTheirTowns = "nothing";

/**
 * What is said under the gauge of a vibe, in the cell of an area. `nothing`: nothing. A
 * cell is small, and its gauge says where the area sits: the founder asked for the words
 * under a gauge to go from a result, and a comparison is many gauges side by side. The
 * band is said in words all the same, by the name of the picture, to whoever hears the
 * page. `words`: where the area sits in words a person would use, and its band, under the
 * gauge, as it was.
 *
 * Either way a band that rests on part of what goes into it says so, in the two words
 * after the mark of what is not whole, and an area a vibe cannot place says so in words.
 */
export type UnderAGauge = "nothing" | "words";

export const UNDER_A_GAUGE_MAY_STAND: readonly UnderAGauge[] = ["nothing", "words"];

/** This is the one line that chooses. */
export const UNDER_A_GAUGE: UnderAGauge = "nothing";

/**
 * Where the pictures of the two ends of a vibe stand. `gauge`: at either end of the gauge
 * of every area, so that each gauge says by itself what its ends are, as the gauge of a
 * result does. `row`: once, at the head of the row, each over the name of its end, and the
 * gauge of an area is its five steps alone: a row is one vibe, so every gauge of it has
 * the same two ends.
 */
export type EndsStand = "gauge" | "row";

export const ENDS_MAY_STAND: readonly EndsStand[] = ["gauge", "row"];

/** This is the one line that chooses. */
export const ENDS_STAND: EndsStand = "gauge";
