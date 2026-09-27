/**
 * The token of a link to sign in, read from the address and taken out of it.
 *
 * A link is `/sign-in/confirm#t=TOKEN`. What follows the `#` is sent to no server by a
 * browser, so the token is in no log of requests and in nothing a host counts. The page
 * reads it here, takes it out of the address bar at once, and holds it in memory alone:
 * it is then in no address a person might copy, and is not what the browser goes back to.
 *
 * This is the one file of the website that changes the address of a page as it stands.
 * It puts a fixed address in its place, which holds nothing: never anything it read.
 *
 * What is not a token as the service makes one is never sent anywhere and never shown.
 */

import { accountPaths } from "./paths";

/** A token as the service makes one: 32 bytes at random, as URL-safe text. */
const A_TOKEN = /^[A-Za-z0-9_-]{43}$/;

/** What stands before a token in the address. */
const BEFORE = "t=";

export type Found =
  /** The address holds nothing after its `#`: the page was opened another way than by a link. */
  | { readonly kind: "none" }
  /** It holds something that is no token: part of the link was lost. */
  | { readonly kind: "not_one" }
  | { readonly kind: "token"; readonly token: string };

/** What a fragment holds. It is handed the fragment, and keeps nothing. */
export function tokenIn(fragment: string): Found {
  const held = fragment.replace(/^#/, "");
  if (held === "") return { kind: "none" };
  const token = held.startsWith(BEFORE) ? held.slice(BEFORE.length) : "";
  return A_TOKEN.test(token) ? { kind: "token", token } : { kind: "not_one" };
}

/**
 * Reads the token from after the `#` of the address, and takes whatever stood there out
 * of the address bar: the address is then that of the page and nothing more. It answers
 * with what it found, which the page holds in memory and hands to nothing but the
 * requests that use it.
 */
export function takeToken(): Found {
  const found = tokenIn(window.location.hash);
  if (found.kind !== "none" || window.location.href.includes("#")) {
    // The address of the page as it is built, with nothing after it. The entry of the
    // history is put in the place of the one that held the token, and none is added.
    window.history.replaceState(window.history.state, "", accountPaths.confirm());
  }
  return found;
}
