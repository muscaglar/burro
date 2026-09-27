/**
 * What a page holds of an account is let go of as the browser puts the page away, and
 * nothing of it is let go of by a page that the browser does not keep.
 */

import { EMAIL, held, standInAccounts } from "../../../test/support/account";
import { forgetAsked, noteAsked, whatWasAsked } from "./asked";
import { forgetAway, isAway, subscribeToAway, watchForAway } from "./away";
import { keepsRecent, noteKeeps } from "./recent";
import { askWho, forgetWho, noteSignedIn, subscribeToWho, whoIs } from "./who";

/** What a browser tells a page as it puts it away, and as it shows it again. */
function told(type: "pagehide" | "pageshow", persisted: boolean): Event {
  const event = new Event(type);
  Object.defineProperty(event, "persisted", { value: persisted });
  return event;
}

beforeEach(() => {
  forgetWho();
  forgetAsked();
  forgetAway();
  noteKeeps(null);
  watchForAway();
});

describe("a page that the browser puts away", () => {
  test("test_who_is_signed_in_what_was_asked_and_what_they_chose_are_let_go_of", () => {
    noteSignedIn(EMAIL);
    noteAsked({ email: EMAIL, minutes: 15 });
    noteKeeps(true);

    window.dispatchEvent(told("pagehide", true));

    expect(whoIs()).toEqual({ kind: "unknown" });
    expect(whatWasAsked()).toBeNull();
    expect(keepsRecent()).toBeNull();
    expect(isAway()).toBe(true);
  });

  test("test_whoever_listens_is_told_at_once_and_before_the_browser_keeps_the_page", () => {
    noteSignedIn(EMAIL);
    const heard: string[] = [];
    subscribeToWho(() => heard.push(`who is ${whoIs().kind}`));
    subscribeToAway(() => heard.push(isAway() ? "away" : "here"));

    window.dispatchEvent(told("pagehide", true));
    // Whatever was heard, was heard by the time the browser was done telling.
    const byThen = [...heard];
    window.dispatchEvent(told("pageshow", true));

    expect(byThen).toEqual(["who is unknown", "away"]);
    expect(heard).toEqual(["who is unknown", "away", "here"]);
    expect(isAway()).toBe(false);
  });

  test("test_a_page_that_the_browser_does_not_keep_lets_go_of_nothing", () => {
    noteSignedIn(EMAIL);
    noteAsked({ email: EMAIL, minutes: 15 });

    // It is loaded anew when a person comes back to it, and holds nothing then.
    window.dispatchEvent(told("pagehide", false));
    window.dispatchEvent(told("pageshow", false));

    expect(whoIs()).toEqual({ kind: "in", email: EMAIL });
    expect(whatWasAsked()).toEqual({ email: EMAIL, minutes: 15 });
    expect(isAway()).toBe(false);
  });

  test("test_an_answer_that_was_on_its_way_as_the_page_was_put_away_is_let_go", async () => {
    const to = standInAccounts(held({ signedIn: true }));
    const waits = to.hold("get_session");
    const asked = askWho(to.client);

    window.dispatchEvent(told("pagehide", true));
    waits.release();
    await asked;

    // It is of the page as it was. Who is signed in is asked again when the page is shown.
    expect(whoIs()).toEqual({ kind: "unknown" });
    to.held.signedIn = false;
    expect(await askWho(to.client)).toEqual({ kind: "out" });
    expect(to.callsTo("get_session")).toHaveLength(2);
  });

  test("test_it_watches_once_however_often_it_is_asked_to", () => {
    const watched = jest.spyOn(window, "addEventListener");

    for (let times = 0; times < 5; times += 1) {
      watchForAway();
      subscribeToAway(() => undefined)();
    }

    expect(watched.mock.calls.filter(([type]) => type === "pagehide" || type === "pageshow")).toEqual([]);
    window.dispatchEvent(told("pagehide", true));
    expect(isAway()).toBe(true);
  });

  test("test_nothing_is_kept_anywhere_and_the_address_of_the_page_is_not_touched", () => {
    const before = window.location.href;
    const entries = window.history.length;
    noteSignedIn(EMAIL);

    window.dispatchEvent(told("pagehide", true));
    window.dispatchEvent(told("pageshow", true));

    expect([window.location.href, window.history.length]).toEqual([before, entries]);
    expect([window.localStorage.length, window.sessionStorage.length, document.cookie]).toEqual([0, 0, ""]);
  });
});
