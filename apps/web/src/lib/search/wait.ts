/**
 * How long a search that begins with no results in sight waits for its answer, at the
 * least, so that Burro is seen to go down his hole and come up again where the results
 * will stand. The founder asked for it: "even if not needed, create a few seconds load
 * time to allow the bunny jumping into a hole animation to appear and take center stage".
 * And, once they had seen it, for it to "last a tad longer".
 *
 * Two numbers say how long, and the wait is the one times the other. How many times he
 * goes down and comes up is `ROUNDS`, here. How long one round of his hop takes is a token
 * of the look, `--motion-hop`, which is what moves him: so he is seen for a whole number
 * of rounds however long the look makes one, and the two cannot part. The token is nought
 * unless the system says that movement is welcome: so where less movement is asked for
 * nothing is waited for, since there is nothing to watch, and one line of the tokens that
 * stills him takes the wait away with his hop.
 *
 * No test of the website waits for it, and none has to say so: a test lays no style sheet,
 * so the length of a round is nought there, as it is wherever nothing moves. A test of the
 * wait itself says how long a round is, as the sheet of the look does.
 *
 * A search that is refined, with its results in sight, waits for nothing.
 */

/**
 * How many times Burro goes down his hole and comes up again before a first answer is
 * shown. Where movement is welcome a round is a second and a quarter, so a first search
 * takes three seconds and three quarters at the least, however fast the service.
 */
export const ROUNDS = 3;

/** The token of the look that says how long one round of his hop takes. */
export const ROUND = "--motion-hop";

/**
 * A length of time, as a style sheet writes one, in milliseconds. What is no length of
 * time is nought: nothing is waited for on words that say nothing.
 */
export function millisecondsOf(said: string): number {
  const found = /^\s*(\d*\.?\d+)(ms|s)\s*$/.exec(said);
  if (found === null) return 0;
  const length = Number(found[1]) * (found[2] === "s" ? 1000 : 1);
  return Number.isFinite(length) ? length : 0;
}

/** How long one round of his hop takes now, as the look says of the page, in milliseconds. */
export function roundNow(): number {
  if (typeof document === "undefined" || typeof getComputedStyle !== "function") return 0;
  return millisecondsOf(getComputedStyle(document.documentElement).getPropertyValue(ROUND));
}

/** How long a first search waits at the least, in milliseconds, asked as the search begins. */
export function leastWait(): number {
  return ROUNDS * roundNow();
}
