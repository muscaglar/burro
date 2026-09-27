/**
 * What is a matter of taste in how a search that came from a link says so, in one line.
 * It is plain code with no state, kept apart from the parts that draw it.
 */

/** Where what says that a search came from a link stands, once the search is open. */
export type NoticeStands = "after" | "over";

export const NOTICE_STANDS_AT: readonly NoticeStands[] = ["after", "over"];

/**
 * `after`: one press away, beside the way to share a search, which stands after the first
 * result. Nothing of it stands over the answer, so the first result of a shared search
 * stands where the first result of any search does. `over`: a notice of one line over the
 * box, which opens in place. It is in sight before anything else of the search, and the
 * first result stands lower by as much as the line is high.
 */
export const NOTICE_STANDS: NoticeStands = "after";
