/**
 * What of the look of Burro was built two ways, each chosen in one line here.
 *
 * Each is a plain value in a file of its own: the parts that draw him run in the browser,
 * and what a page takes from such a file is a component and nothing else.
 */

/**
 * What he does where nothing is asked of him, which is where he sits: beside the heading
 * and in what every page stands in. `stirs`: he is never still for long. An ear twitches, his
 * nose goes, he blinks, he shifts his weight, and now and then he looks round or washes an
 * ear. `still`: he is drawn still, as he was until a person who walked the website asked
 * for him to move.
 *
 * Neither changes what he does while a search is read: he hops, until the answer is in.
 * And neither moves him where the system asks for less movement: he is still there.
 */
export type AtRest = "stirs" | "still";

export const AT_REST: AtRest = "stirs";

/**
 * What flies as he hops. `flicks`: as he goes down his hole soil flicks up and out of it, a
 * few crumbs that rise, spread and fall, and again as he comes up: a person who watched him
 * hop asked for it. `none`: nothing flies, and he hops as he did.
 *
 * Neither draws soil where he is still. Where the system asks for less movement he waits
 * beside his hole, and nothing flies.
 */
export type Soil = "flicks" | "none";

export const SOIL: Soil = "flicks";
