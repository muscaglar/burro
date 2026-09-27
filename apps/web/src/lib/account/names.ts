/**
 * The names that pass between the website and the service for accounts: two headers the
 * website adds, two cookies the service sets, and the one header a page sends with
 * everything that changes something. The service reads and writes them by the same names.
 *
 * They are names and no more. None is a secret, and the secret itself is in no file.
 */

/**
 * The header in which the website says that it is the website, by a secret both read from
 * their environment. The service answers the routes of accounts to nobody else. It is
 * sent to the service and to nothing else, and never to a browser.
 */
export const WEBSITE_HEADER = "X-Burro-Website";

/**
 * The header in which the website says what the address of the client is, as the
 * website's host gave it. The service believes it from the website alone. A header of
 * this name that a client sent is never passed on.
 */
export const CLIENT_HEADER = "X-Burro-Client-Address";

/**
 * The header a page sends with every request that changes anything. A form on another
 * site cannot send it, and a page of another site may not without being let.
 */
export const REQUEST_HEADER = "X-Burro-Request";
export const REQUEST_VALUE = "1";

/** The cookie that holds a session. No script can read it, and the website never tries. */
export const SESSION_COOKIE = "__Host-burro_session";

/** The cookie that binds a link to the browser that asked for it, for as long as the link lasts. */
export const LINK_COOKIE = "__Host-burro_link";

/** The cookies the website lets by, both ways. Any other is dropped. */
export const COOKIES: readonly string[] = [SESSION_COOKIE, LINK_COOKIE];

/**
 * The same two as they are named in development, where the website is in the clear on a
 * machine of one's own: a browser takes neither the prefix nor a cookie that is kept from
 * the clear there. They are let by there and nowhere else.
 */
export const COOKIES_IN_THE_CLEAR: readonly string[] = ["burro_session", "burro_link"];
