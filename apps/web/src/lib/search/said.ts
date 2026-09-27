/**
 * What the page says of a reading once Burro has taken what it noticed: the service's
 * notice, and what Burro left out. It is plain code with no state.
 *
 * Every word here is the service's, as it came. Nothing that was typed is here.
 */

import { LEFT_OUT } from "@/content/search";
import type { RejectReason } from "@/lib/api/schema";

import type { Refusal } from "./refusals";
import type { Left, Read } from "./state";
import type { WhyLeft } from "./takes";

/**
 * Why a thing is named in the line of what was left out: why Burro left what it noticed,
 * or `range`, that a number the words gave is outside what Burro takes.
 */
export type WhyNamed = WhyLeft | "range";

/** Where one sentence ends and the next begins. */
const BETWEEN_SENTENCES = /(?<=[.!?])\s+/;

/**
 * The service's notice, as the page shows it. It is shown as it came, word for word, but
 * in one case. The service writes its notice of the words as it read them, and of words
 * that are no plain list it ends by saying that nothing of them has changed the search.
 * Where Burro then takes what was noticed in those very words, that last sentence is true
 * no longer, and is left out: every sentence before it is shown whole, as it came. What
 * the notice is there to say, which is what Burro ranks by, is never left out.
 */
export function noticeOf(read: Pick<Read, "notice" | "notice_text" | "changed" | "took">): string {
  if (read.notice === "none" || read.changed || read.took === 0) return read.notice_text;
  const sentences = read.notice_text.split(BETWEEN_SENTENCES);
  return sentences.length < 2 ? read.notice_text : sentences.slice(0, -1).join(" ");
}

/** One thing Burro noticed and left out of the search, as the line beside the box names it. */
export interface LeftThing {
  /** By what it is told from every other thing of the line. */
  readonly key: string;
  /** Its name, which is the service's, or the page's own where the service's holds a figure. */
  readonly name: string;
  readonly why: WhyNamed;
  /** Why, in the service's own words, where it gave no way to take the thing. Empty of every other. */
  readonly says: string;
}

/**
 * What a thing is called. The name the service gives a budget holds the amount that was
 * typed, and the name of a journey may hold its minutes: a name that holds a figure is
 * not said, and the page names the thing itself, as it names a setting. What was typed is
 * drawn in the box and nowhere else.
 *
 * A rule for an area bears the name of the area, which among what was left out reads as
 * an area that was left out of the results. The page says what was left out: what to do
 * with the area. So it is with a journey that waits for a person, which bears the name of
 * its place: what was left out is the journey there.
 */
function nameOf({ target, label, why }: Pick<Left, "target" | "label" | "why">): string {
  if (why === "area") return LEFT_OUT.ofAnArea(label);
  if (why === "journey" && !/\d/.test(label)) return LEFT_OUT.ofAJourney(label);
  if (!/\d/.test(label)) return label;
  if (target === "budget" || target === "tenure") return LEFT_OUT.named_by_the_page.budget;
  if (target === "commute") return LEFT_OUT.named_by_the_page.commute;
  return label;
}

/**
 * What Burro noticed and left out of the search, each thing once, in the order it was
 * noticed: what counts recorded crime or who lived somewhere, a journey to a place Burro
 * does not know, a thing the service gave no way to take, a rule for an area and a thing
 * that runs two ways, where the words give no way of it. The page names them in one line,
 * and says why of each once the line is opened.
 */
export function leftOutOf(read: Pick<Read, "left"> | null): readonly LeftThing[] {
  const things = (read?.left ?? []).flatMap((one, at): LeftThing[] => {
    // What the service has a person know of a thing stands after what it says of it.
    const says =
      one.why === "no_way" ? [one.does, one.follows, one.note].filter((words) => words !== "").join(" ") : "";
    if (one.label === "" || (one.why === "no_way" && says === "")) return [];
    const name = nameOf(one);
    // A thing the page names itself is told from another of its kind by where it stood,
    // but a rule for an area and a journey that waits, which are told by the name of the
    // area and of the place.
    const byItsLabel = name === one.label || one.why === "area" || name === LEFT_OUT.ofAJourney(one.label);
    return [{ key: byItsLabel ? `${one.why} ${one.label}` : `${one.why} ${name} ${at}`, name, why: one.why, says }];
  });
  return things.filter((thing, at) => things.findIndex((one) => one.key === thing.key) === at);
}

/**
 * The reasons an edit of a sentence is refused for that the line of what was left out
 * names, and what the line says of each: a place Burro does not know, which it names
 * already where the service offered the journey, and a number that is outside what Burro
 * takes.
 */
const NAMED_WHERE_REFUSED: Partial<Record<RejectReason, WhyNamed>> = {
  unknown_place: "place",
  out_of_range: "range",
};

/** What such a refusal is called, by the part it was about, or `null` where the page has no name for it. */
function nameOfRefused(key: Refusal["key"], nameOf: (key: string) => string | null): string | null {
  if (key === null) return null;
  const named = nameOf(key);
  // A journey is named as the journey to its place, and where the answers gave the place
  // no name, as a journey: the id of a place is never drawn, and is no name.
  if (key.startsWith("place:")) return named === null ? LEFT_OUT.named_by_the_page.commute : LEFT_OUT.ofAJourney(named);
  return key === "budget" ? LEFT_OUT.named_by_the_page.budget : named;
}

/**
 * What a sentence asked for and Burro refused for its place or its number, as the line of
 * what was left out names it, and every other refusal, which is said where it was. Under
 * what Burro understood each was a line of its own, with no control beside it to show
 * which place or which number it spoke of: "That number is outside what Burro accepts."
 * Said in full there, with what Burro did and where to go on, it stood over the answer,
 * and the first result ended under the first screen of a phone. In the line it is named,
 * and why is one press away. A refusal the page has no name for is left where it was.
 */
export function refusedOf(
  refusals: readonly Refusal[],
  nameOf: (key: string) => string | null,
): { readonly named: readonly LeftThing[]; readonly rest: readonly Refusal[] } {
  const named: LeftThing[] = [];
  const rest: Refusal[] = [];
  refusals.forEach((refusal, at) => {
    const why = NAMED_WHERE_REFUSED[refusal.reason];
    const name = why === undefined ? null : nameOfRefused(refusal.key, nameOf);
    if (why === undefined || name === null) rest.push(refusal);
    // Two journeys may bear one name, so each is told by where it stood among the refusals.
    else named.push({ key: `refused ${why} ${name} ${at}`, name, why, says: "" });
  });
  return { named, rest };
}
