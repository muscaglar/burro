/**
 * The token of a link to sign in is read from after the `#` of the address, and taken out
 * of the address at once. What is not a token as the service makes one is never handed on.
 */

import { TOKEN } from "../../../test/support/account";
import { accountPaths } from "./paths";
import { takeToken, tokenIn } from "./token";

const CANARY = "zqxcanary7431";
const PAGE = accountPaths.confirm();

/** Puts the browser of the test at an address, as opening a link does. */
function at(address: string): void {
  window.history.pushState(null, "", address);
}

afterEach(() => at("/"));

describe("the token of a link", () => {
  test("test_a_token_is_read_from_after_the_hash", () => {
    expect(tokenIn(`#t=${TOKEN}`)).toEqual({ kind: "token", token: TOKEN });
    expect(tokenIn(`t=${TOKEN}`)).toEqual({ kind: "token", token: TOKEN });
    expect(TOKEN).toHaveLength(43);
  });

  test("test_an_address_with_nothing_after_its_hash_holds_no_link", () => {
    expect(tokenIn("")).toEqual({ kind: "none" });
    expect(tokenIn("#")).toEqual({ kind: "none" });
  });

  test.each([
    `#${TOKEN}`,
    `#t=${TOKEN.slice(1)}`,
    `#t=${TOKEN}x`,
    `#t=${TOKEN}&next=/account`,
    `#t=${TOKEN.slice(0, 42)}!`,
    `#t=${TOKEN.slice(0, 42)}=`,
    `#T=${TOKEN}`,
    `#token=${TOKEN}`,
    "#t=",
    `#t=${CANARY}`,
    `#t=${"a".repeat(128)}`,
    "#t=https://elsewhere.example/",
    `#next=https://elsewhere.example/&t=${TOKEN}`,
  ])("test_what_is_no_token_as_the_service_makes_one_is_never_handed_on: %#", (fragment) => {
    const found = tokenIn(fragment);

    expect(found).toEqual({ kind: "not_one" });
    expect(JSON.stringify(found)).not.toContain(CANARY);
  });

  test("test_the_token_is_taken_out_of_the_address_at_once_and_no_entry_is_added_to_the_history", () => {
    at(`${PAGE}#t=${TOKEN}`);
    const entries = window.history.length;
    const replaced = jest.spyOn(window.history, "replaceState");
    const pushed = jest.spyOn(window.history, "pushState");

    const found = takeToken();

    expect(found).toEqual({ kind: "token", token: TOKEN });
    expect(window.location.href).toBe(`http://localhost${PAGE}`);
    expect(window.location.hash).toBe("");
    // The entry that held the token is replaced: going back does not lead to it.
    expect(replaced).toHaveBeenCalledTimes(1);
    expect(pushed).not.toHaveBeenCalled();
    expect(window.history.length).toBe(entries);
    // What is put in its place is the address of the page, which holds nothing that was read.
    expect(JSON.stringify(replaced.mock.calls).includes(TOKEN)).toBe(false);
    expect(replaced.mock.calls[0]?.[2]).toBe(PAGE);
  });

  test("test_what_is_no_token_is_taken_out_of_the_address_all_the_same", () => {
    at(`${PAGE}#t=${CANARY}`);

    expect(takeToken()).toEqual({ kind: "not_one" });
    expect(window.location.href).toBe(`http://localhost${PAGE}`);
    expect(window.location.href.includes(CANARY)).toBe(false);
  });

  test("test_an_address_that_holds_nothing_is_left_as_it_is", () => {
    at(PAGE);
    const replaced = jest.spyOn(window.history, "replaceState");

    expect(takeToken()).toEqual({ kind: "none" });
    expect(replaced).not.toHaveBeenCalled();
  });

  test("test_once_taken_it_is_not_found_a_second_time", () => {
    at(`${PAGE}#t=${TOKEN}`);

    expect(takeToken().kind).toBe("token");
    expect(takeToken()).toEqual({ kind: "none" });
  });

  test("test_what_the_history_held_for_the_page_is_handed_back_as_it_was", () => {
    // The router keeps what it needs of a page in the entry of the history. It is put back unread.
    window.history.pushState({ kept: "by the router" }, "", `${PAGE}#t=${TOKEN}`);

    takeToken();

    expect(window.history.state).toEqual({ kept: "by the router" });
  });
});
