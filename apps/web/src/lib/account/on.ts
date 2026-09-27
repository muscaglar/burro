/**
 * Whether accounts are on. One setting says so, and they are off unless it says `on`.
 *
 * With them off the website is what it was before there were accounts: no entry in the
 * name board, no button on the search page, no page of an account, and a route that
 * passes nothing on. Every part of accounts asks here first, and nowhere else.
 *
 * It is no secret: whether a person can sign in is plain from the name board. So it is a
 * setting that the browser's code may hold, which lets a part that runs in the browser
 * ask without being handed it. It is read when the website is built, so a change does
 * nothing until the website is built again.
 */

export const ACCOUNTS_VARIABLE = "NEXT_PUBLIC_BURRO_ACCOUNTS";

/** The one value that turns accounts on. Anything else, and nothing at all, leaves them off. */
export const ON = "on";

export function accountsOn(): boolean {
  // Written out in full, because Next puts the value into the browser's code
  // only where it finds the name spelt like this.
  return process.env.NEXT_PUBLIC_BURRO_ACCOUNTS === ON;
}
