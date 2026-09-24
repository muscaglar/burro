import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CHIPS } from "@/content/search";
import { SHARE } from "@/content/share";
import { createClient, type Answer } from "@/lib/api/client";
import { recordedAnswer, recordedError, responseFrom } from "@/lib/api/recorded";
import type { PreferenceSpec, ShareCreated } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { linkTo, SharePanel } from "./SharePanel";

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const made = recordedAnswer("create_share", "share-made");
const exact = recordedAnswer("create_share", "share-made-exact");
const sentSpec = (made.request.body as { spec: PreferenceSpec }).spec;
const noPlaces: PreferenceSpec = { ...sentSpec, commutes: [] };
const ORIGIN = window.location.origin;

/**
 * How long the stand-in takes to answer, in milliseconds. A service answers a moment after
 * it is asked, and never at once. On a quick machine an answer that came at once had landed
 * by the next line of a test, and on a slower one it had not: so the stand-in is always a
 * moment late, and a test that does not wait for what it looks for fails everywhere.
 */
const A_MOMENT = 25;

/** Answers as the API does, from a recording and a moment later, and keeps what it was asked. */
function creating(scenario = "share-made") {
  const asked: boolean[] = [];
  const client = createClient({
    baseUrl: "https://api.example.test",
    fetch: (async () => {
      await new Promise((resolve) => setTimeout(resolve, A_MOMENT));
      return responseFrom(
        scenario.startsWith("share") ? recordedAnswer("create_share", scenario) : recordedError(scenario),
      );
    }) as typeof fetch,
  });
  const create = (exactPlaces: boolean): Promise<Answer<ShareCreated>> => {
    asked.push(exactPlaces);
    return client.createShare({ spec: sentSpec, exact_destinations: exactPlaces });
  };
  return { asked, create };
}

function show(create: ReturnType<typeof creating>["create"], spec = sentSpec, specHash: string | null = "hash-one") {
  const user = userEvent.setup({ delay: null });
  const panel = (nextSpec = spec, nextHash = specHash) => (
    <SharePanel
      spec={nextSpec}
      specHash={nextHash}
      meta={meta}
      areas={areas}
      create={create}
    />
  );
  const view = render(panel());
  return { user, panel, ...view };
}

async function opened(scenario = "share-made", spec = sentSpec) {
  const api = creating(scenario);
  const view = show(api.create, spec);
  await view.user.click(screen.getByRole("button", { name: SHARE.open }));
  return { ...api, ...view };
}

const field = () => screen.queryByRole<HTMLInputElement>("textbox", { name: SHARE.link });

/**
 * Presses the button that makes a link, and waits for what the service answers.
 *
 * The link is made by a call that answers a moment later. While it is made the button says
 * so, and once the answer has landed it no longer does: that is what is waited for, whether
 * the answer is a link or a failure.
 */
async function make(user: ReturnType<typeof userEvent.setup>, name: string = SHARE.make) {
  await user.click(screen.getByRole("button", { name }));
  await waitFor(() => expect(screen.queryByRole("button", { name: SHARE.making })).toBeNull());
}

describe("what a share is said to hold, before it is made", () => {
  test("test_the_panel_is_closed_at_first_and_opens_in_place", async () => {
    const { user } = show(creating().create);

    expect(screen.getByRole("button", { name: SHARE.open })).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByText(SHARE.holds.title)).toBeNull();

    await user.click(screen.getByRole("button", { name: SHARE.open }));

    expect(screen.getByRole("button", { name: SHARE.open })).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("region", { name: SHARE.holds.title })).toBeInTheDocument();
  });

  test("test_the_panel_says_what_a_link_holds_before_any_link_is_made", async () => {
    const { asked } = await opened();

    for (const point of SHARE.holds.points) expect(screen.getByText(point)).toBeInTheDocument();
    expect(asked).toEqual([]);
    expect(field()).toBeNull();
  });

  test("test_the_panel_says_that_places_are_replaced_unless_the_person_chooses_otherwise", async () => {
    await opened();

    const box = screen.getByRole("checkbox", { name: SHARE.exact.label });

    expect(box).not.toBeChecked();
    expect(box).toHaveAccessibleDescription(SHARE.exact.hint);
    expect(SHARE.exact.hint).toMatch(/station or district/);
  });

  test("test_a_search_that_names_no_place_offers_no_choice_of_places", async () => {
    const { user, asked } = await opened("share-made", noPlaces);

    expect(screen.queryByRole("checkbox")).toBeNull();
    expect(screen.getByText(SHARE.noPlaces)).toBeInTheDocument();
    await make(user);
    expect(asked).toEqual([false]);
  });
});

describe("making a link", () => {
  test("test_the_link_is_the_websites_address_with_the_id_in_its_fragment_and_nothing_else", async () => {
    const { user } = await opened();

    await make(user);

    const link = new URL(field()?.value ?? "");
    expect(link.origin).toBe(ORIGIN);
    expect(link.pathname).toBe("/s");
    expect(link.search).toBe("");
    expect(link.hash).toBe(`#${made.body.data.share_id}`);
    expect(screen.getByRole("status")).toHaveTextContent(SHARE.made);
  });

  test("test_places_are_replaced_unless_the_box_is_ticked", async () => {
    const { user, asked } = await opened();

    await make(user);
    await user.click(screen.getByRole("checkbox", { name: SHARE.exact.label }));
    await make(user, SHARE.makeAgain);

    expect(asked).toEqual([false, true]);
  });

  test("test_a_link_whose_places_were_replaced_says_the_ranking_may_differ", async () => {
    const { user } = await opened("share-made");

    await make(user);

    expect(made.body.data.coarsened).toBe(true);
    expect(screen.getByText(SHARE.coarsened)).toBeInTheDocument();
    expect(screen.queryByText(SHARE.exactKept)).toBeNull();
  });

  test("test_a_link_that_holds_the_exact_places_says_so", async () => {
    const { user } = await opened("share-made-exact");

    await user.click(screen.getByRole("checkbox", { name: SHARE.exact.label }));
    await make(user);

    expect(exact.body.data.coarsened).toBe(false);
    expect(screen.getByText(SHARE.exactKept)).toBeInTheDocument();
    expect(screen.queryByText(SHARE.coarsened)).toBeNull();
  });

  test("test_a_link_whose_places_needed_no_replacing_does_not_say_the_choice_was_ignored", async () => {
    // Seen in a browser: the box was left unticked, the one place was a district, which stands
    // in for itself, and the panel said "The link holds the places as you named them."
    const { user, asked } = await opened("share-made-exact");

    await make(user);

    expect(asked).toEqual([false]);
    expect(exact.body.data.coarsened).toBe(false);
    expect(screen.getByText(SHARE.noneReplaced)).toBeInTheDocument();
    expect(screen.queryByText(SHARE.exactKept)).toBeNull();
    expect(screen.queryByText(SHARE.coarsened)).toBeNull();
    expect(SHARE.noneReplaced).toMatch(/station or a district/);
  });

  test("test_the_button_is_never_switched_off_so_that_it_never_drops_the_focus", async () => {
    // Seen in a browser: after "Make the link" the focus was on nothing. The button was
    // switched off while the link was made, and a button that is switched off loses the
    // focus. A stand-in for a browser leaves it there, so this holds the button itself.
    let answer: (value: Answer<ShareCreated>) => void = () => undefined;
    const create = jest.fn(() => new Promise<Answer<ShareCreated>>((resolve) => (answer = resolve)));
    const { user } = show(create);
    await user.click(screen.getByRole("button", { name: SHARE.open }));

    await user.click(screen.getByRole("button", { name: SHARE.make }));
    const making = screen.getByRole("button", { name: SHARE.making });

    expect(making).not.toBeDisabled();
    expect(making).toHaveAttribute("aria-disabled", "true");
    expect(making).toHaveFocus();
    // A second press while the link is being made asks for nothing more.
    await user.click(making);
    expect(create).toHaveBeenCalledTimes(1);
    answer(await creating().create(false));
    await waitFor(() => expect(field()).not.toBeNull());
    expect(screen.getByRole("button", { name: SHARE.makeAgain })).toHaveFocus();
  });

  test("test_a_link_that_was_made_before_the_page_was_left_is_there_when_it_is_come_back_to", async () => {
    // Seen in a browser: the link was gone after the page of an area was read, so a second
    // link had to be made of the same search.
    const held = { of: "hash-one", exact: false, share: made.body.data };
    const user = userEvent.setup({ delay: null });
    render(
      <SharePanel
        spec={sentSpec}
        specHash="hash-one"
        meta={meta}
        areas={areas}
        create={creating().create}
        held={held}
      />,
    );

    // The panel is open, because it holds something.
    expect(screen.getByRole("button", { name: SHARE.open })).toHaveAttribute("aria-expanded", "true");
    expect(field()?.value).toBe(linkTo(made.body.data.share_id, ORIGIN));
    expect(screen.getByRole("button", { name: SHARE.makeAgain })).toBeInTheDocument();
    expect(user).toBeDefined();
  });

  test("test_a_link_that_was_made_of_another_search_is_not_shown_when_the_page_is_come_back_to", () => {
    const held = { of: "hash-of-another", exact: false, share: made.body.data };
    render(
      <SharePanel
        spec={sentSpec}
        specHash="hash-one"
        meta={meta}
        areas={areas}
        create={creating().create}
        held={held}
      />,
    );

    expect(screen.getByRole("button", { name: SHARE.open })).toHaveAttribute("aria-expanded", "false");
    expect(field()).toBeNull();
  });

  test("test_the_settings_the_link_holds_are_shown_as_the_api_stored_them", async () => {
    const { user } = await opened("share-made");

    await make(user);
    const stored = screen.getByRole("heading", { name: SHARE.stored }).nextElementSibling as HTMLElement;
    const chips = within(stored).getAllByRole("listitem").map((chip) => chip.textContent);

    expect(chips).toContain("Renting");
    expect(chips).toContain(`Usual settings: 6 ${CHIPS.assumed}`);
    expect(chips.some((chip) => chip?.startsWith("£1,700 a month"))).toBe(true);
    expect(chips).toContain("Leafy");
    // The place that was stored is not the one that was named. It is shown by its own name,
    // which the answer gives, and the one that was named is not.
    expect(made.body.data.spec.commutes[0]?.place_id).not.toBe(sentSpec.commutes[0]?.place_id);
    expect(made.body.data.places.map((place) => place.name)).toEqual(["Eskerfold"]);
    expect(chips.some((chip) => chip?.startsWith("Eskerfold"))).toBe(true);
    expect(stored.textContent?.includes("Alderwick Primary School")).toBe(false);
    expect(/Place \d/.test(stored.textContent ?? "")).toBe(false);
  });

  test("test_a_place_that_was_kept_as_named_is_shown_by_its_name", async () => {
    const { user } = await opened("share-made-exact");

    await user.click(screen.getByRole("checkbox", { name: SHARE.exact.label }));
    await make(user);
    const stored = screen.getByRole("heading", { name: SHARE.stored }).nextElementSibling as HTMLElement;

    expect(stored.textContent?.includes("Alderwick Primary School")).toBe(true);
  });

  test("test_a_link_made_of_an_earlier_search_is_not_shown_for_this_one", async () => {
    const { user, rerender, panel } = await opened();
    await make(user);
    expect(field()).not.toBeNull();

    rerender(panel(noPlaces, "hash-two"));

    expect(field()).toBeNull();
    expect(screen.getByRole("button", { name: SHARE.make })).toBeInTheDocument();
  });

  test("test_the_field_that_holds_the_link_cannot_be_sent_or_kept_by_the_browser", async () => {
    const { user, container } = await opened();

    await make(user);

    expect(field()).toHaveAttribute("readonly");
    expect(field()).not.toHaveAttribute("name");
    expect(field()).toHaveAttribute("autocomplete", "off");
    expect(container.querySelector("form")).toBeNull();
    // The link is text to copy. Nothing on the page leads to it, so nothing is fetched from it.
    expect(container.querySelector("a[href*='/s']")).toBeNull();
  });
});

describe("copying a link", () => {
  function clipboard(writeText: (text: string) => Promise<void>) {
    Object.defineProperty(window.navigator, "clipboard", { configurable: true, value: { writeText } });
  }

  afterEach(() => {
    Reflect.deleteProperty(window.navigator, "clipboard");
  });

  test("test_copying_puts_the_link_on_the_clipboard_and_says_so", async () => {
    const { user } = await opened();
    await make(user);
    const copied: string[] = [];
    clipboard(async (text) => void copied.push(text));

    await user.click(screen.getByRole("button", { name: SHARE.copy }));

    // The browser copies in its own time, so what is said of it is waited for.
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent(SHARE.copied));
    expect(copied).toEqual([`${ORIGIN}/s#${made.body.data.share_id}`]);
  });

  test("test_where_the_browser_will_not_copy_the_link_is_selected_for_the_person_to_copy", async () => {
    const { user } = await opened();
    await make(user);
    clipboard(async () => {
      throw new Error("not allowed");
    });

    await user.click(screen.getByRole("button", { name: SHARE.copy }));

    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent(SHARE.notCopied));
    expect(field()).toHaveFocus();
    expect([field()?.selectionStart, field()?.selectionEnd]).toEqual([0, field()?.value.length]);
  });

  test("test_a_browser_with_no_clipboard_does_not_break_the_page", async () => {
    const { user } = await opened();
    await make(user);
    Reflect.deleteProperty(window.navigator, "clipboard");

    await user.click(screen.getByRole("button", { name: SHARE.copy }));

    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent(SHARE.notCopied));
  });
});

describe("a link that cannot be made", () => {
  test("test_a_failure_is_said_in_the_apis_words_with_the_id_to_quote", async () => {
    const failure = recordedError("error-internal");
    const { user } = await opened("error-internal");

    await make(user);

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(SHARE.failed);
    expect(alert).toHaveTextContent(failure.body.error.message);
    expect(alert).toHaveTextContent(failure.headers["x-request-id"] ?? "no id");
    expect(field()).toBeNull();
    // It can be tried again with the same button.
    expect(screen.getByRole("button", { name: SHARE.make })).toBeEnabled();
  });

  test("test_an_id_that_is_not_one_the_api_makes_is_never_put_in_an_address", () => {
    expect(linkTo("KwduC18xc41r0W0schExDw", "https://burro.example")).toBe(
      "https://burro.example/s#KwduC18xc41r0W0schExDw",
    );
    for (const id of ["", "short", "zqxcanary7431 and quiet", "KwduC18xc41r0W0schExDw/../x", "a".repeat(23)]) {
      expect(linkTo(id, "https://burro.example")).toBeNull();
    }
  });
});

describe("the share panel, to a screen reader", () => {
  test.each([
    ["before a link is made", false],
    ["with a link made", true],
  ])("test_the_panel_has_no_accessibility_fault_%s", async (_, link) => {
    const { user, container } = await opened();
    if (link) await make(user);

    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_every_control_of_the_panel_takes_a_target_size", async () => {
    const { user, container } = await opened();
    await make(user);

    const controls = [...container.querySelectorAll("button, input[type='checkbox'], a")];

    expect(controls).toHaveLength(4);
    expect(
      controls.filter((control) => !control.classList.contains("target") && !control.classList.contains("target-min")),
    ).toEqual([]);
  });
});

describe("a service that answers a moment later", () => {
  test("test_nothing_of_a_link_is_on_the_page_until_the_service_has_answered", async () => {
    // Seen on a slower machine: a test pressed "Make the link" and read the field on its next
    // line. The answer had not landed, so there was no field to read. The stand-in of this
    // suite is always a moment late, so that a test which does not wait fails everywhere.
    const { user } = await opened();

    await user.click(screen.getByRole("button", { name: SHARE.make }));

    expect(A_MOMENT).toBeGreaterThan(0);
    expect(field()).toBeNull();
    expect(screen.getByRole("button", { name: SHARE.making })).toBeInTheDocument();
    expect(await screen.findByRole("textbox", { name: SHARE.link })).toHaveValue(
      linkTo(made.body.data.share_id, ORIGIN) ?? "no link",
    );
  });
});
