/**
 * Who is signed in, as the service last said: asked once, held in memory, and heard from
 * whatever signs a person in or out.
 */

import { EMAIL, held, standInAccounts } from "../../../test/support/account";
import { forgetStands, isTheirs, keepsRecent, noteKeeps, noteStands } from "./recent";
import { askWho, forgetWho, notePutAway, noteSignedIn, noteSignedOut, subscribeToWho, whoIs } from "./who";

beforeEach(() => {
  forgetWho();
  noteKeeps(null);
  forgetStands();
});

describe("who is signed in", () => {
  test("test_nothing_is_known_until_the_service_has_said", async () => {
    const to = standInAccounts(held({ signedIn: true }));

    expect(whoIs()).toEqual({ kind: "unknown" });
    expect(to.calls).toEqual([]);

    expect(await askWho(to.client)).toEqual({ kind: "in", email: EMAIL });
    expect(whoIs()).toEqual({ kind: "in", email: EMAIL });
  });

  test("test_nobody_is_signed_in_where_the_service_says_so", async () => {
    const to = standInAccounts(held({ signedIn: false }));

    expect(await askWho(to.client)).toEqual({ kind: "out" });
  });

  test("test_two_that_ask_at_once_are_one_request", async () => {
    const to = standInAccounts(held({ signedIn: true }));

    const [one, other] = await Promise.all([askWho(to.client), askWho(to.client)]);

    expect([one, other]).toEqual([
      { kind: "in", email: EMAIL },
      { kind: "in", email: EMAIL },
    ]);
    expect(to.callsTo("get_session")).toHaveLength(1);
    // Once it has answered, it may be asked again.
    await askWho(to.client);
    expect(to.callsTo("get_session")).toHaveLength(2);
  });

  test("test_a_service_that_could_not_say_is_not_taken_to_have_said_that_nobody_is_signed_in", async () => {
    const to = standInAccounts(held({ signedIn: true })).unreachable("get_session");

    expect(await askWho(to.client)).toMatchObject({ kind: "unsaid", failure: { kind: "network" } });

    to.asHeld("get_session");
    expect(await askWho(to.client)).toEqual({ kind: "in", email: EMAIL });
  });

  test("test_a_sign_in_and_a_sign_out_are_heard_at_once_and_whoever_listens_is_told", () => {
    const told: string[] = [];
    const stop = subscribeToWho(() => told.push(whoIs().kind));

    noteSignedIn(EMAIL);
    noteSignedIn(EMAIL);
    noteSignedOut();
    stop();
    noteSignedIn(EMAIL);

    // Told once for each change, and not again for what was known already.
    expect(told).toEqual(["in", "out"]);
    expect(whoIs()).toEqual({ kind: "in", email: EMAIL });
  });

  test("test_an_answer_that_was_asked_for_before_a_sign_in_does_not_unsay_it", async () => {
    const to = standInAccounts(held({ signedIn: false }));
    const waits = to.hold("get_session");

    const asked = askWho(to.client);
    noteSignedIn(EMAIL);
    waits.release();

    expect(await asked).toEqual({ kind: "in", email: EMAIL });
    expect(whoIs()).toEqual({ kind: "in", email: EMAIL });
  });

  test("test_whether_the_last_searches_are_kept_is_let_go_of_as_the_person_who_is_signed_in_changes", async () => {
    const to = standInAccounts(held({ signedIn: true }));
    await askWho(to.client);
    noteKeeps(true);

    // The same person, said again: what was learned of them stands.
    await askWho(to.client);
    noteSignedIn(EMAIL);
    expect(keepsRecent()).toBe(true);

    // Somebody else signed in, in another tab of the browser: it was learned of the one before.
    to.held.email = "juniper.vale@example.org";
    await askWho(to.client);
    expect(whoIs()).toEqual({ kind: "in", email: "juniper.vale@example.org" });
    expect(keepsRecent()).toBeNull();
  });

  test("test_the_search_that_stands_is_not_theirs_who_signs_in_after_it_was_made", async () => {
    const to = standInAccounts(held({ signedIn: true }));
    await askWho(to.client);
    const ranking = {};
    noteStands(ranking, true);

    // The same person, said again: what they made is theirs still.
    await askWho(to.client);
    noteSignedIn(EMAIL);
    expect(isTheirs(ranking)).toBe(true);

    // Somebody else signed in, in another tab of the browser. It is not made theirs by being seen again.
    to.held.email = "juniper.vale@example.org";
    await askWho(to.client);
    noteStands(ranking, true);
    expect(isTheirs(ranking)).toBe(false);
  });

  test.each([
    ["signs out", () => noteSignedOut()],
    ["leaves the page for the browser to keep", () => notePutAway()],
  ])("test_the_search_that_stands_is_nobodys_to_have_kept_once_the_person_who_made_it_%s", async (_, leaves) => {
    const to = standInAccounts(held({ signedIn: true }));
    await askWho(to.client);
    const ranking = {};
    noteStands(ranking, true);

    leaves();
    // They sign in again, or somebody else does: the page cannot tell which.
    await askWho(to.client);

    expect(whoIs()).toEqual({ kind: "in", email: EMAIL });
    expect(isTheirs(ranking)).toBe(false);
  });

  test("test_a_search_that_was_made_while_nobody_was_signed_in_is_not_theirs_who_signs_in_next", async () => {
    const to = standInAccounts(held({ signedIn: false }));
    await askWho(to.client);
    const ranking = {};
    noteStands(ranking, false);

    to.held.signedIn = true;
    await askWho(to.client);
    noteStands(ranking, true);

    expect(isTheirs(ranking)).toBe(false);
    // What they make once they are signed in is theirs.
    const next = {};
    noteStands(next, true);
    expect([isTheirs(next), isTheirs(ranking)]).toEqual([true, false]);
  });

  test("test_what_is_held_is_the_address_and_nothing_else_of_the_account", async () => {
    const to = standInAccounts(held({ signedIn: true }));

    const who = await askWho(to.client);

    expect(Object.keys(who).sort()).toEqual(["email", "kind"]);
  });
});
