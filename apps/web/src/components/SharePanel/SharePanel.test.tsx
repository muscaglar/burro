import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CHIPS } from "@/content/search";
import { SHARE } from "@/content/share";
import { createClient, type Answer } from "@/lib/api/client";
import { recordedAnswer, recordedError, responseFrom } from "@/lib/api/recorded";
import type { PreferenceSpec, ShareCreated } from "@/lib/api/schema";

import { chipsOf } from "@/lib/search/chips";
import { namesOf } from "@/lib/search/state";
import { HEAD } from "@/lib/sight";

import { faultsIn } from "../../../test/support/axe";
import { heavier, rulesOf, weightOf } from "../../../test/support/css";
import { stateOf, thingOf } from "../ChipRow/drawn";
import { drawingOf } from "../kit/Thing/drawn";
import { WHAT_IT_OPENS, WHAT_IT_OPENS_MAY_BE, type WhatItOpens } from "./look";
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

/**
 * A share as it was recorded, with its first vibe made one that Burro filled in and nobody
 * said: no share was recorded with one, and a link may hold one.
 */
const INFERRED = "share-made, with a vibe nobody said";
const madeWithAnInferredVibe = {
  ...made,
  body: {
    ...made.body,
    data: {
      ...made.body.data,
      spec: {
        ...made.body.data.spec,
        tags: made.body.data.spec.tags.map((tag, at) => (at === 0 ? { ...tag, provenance: "inferred" as const } : tag)),
      },
    },
  },
};

/** Answers as the API does, from a recording and a moment later, and keeps what it was asked. */
function creating(scenario = "share-made") {
  const asked: boolean[] = [];
  const client = createClient({
    baseUrl: "https://api.example.test",
    fetch: (async () => {
      await new Promise((resolve) => setTimeout(resolve, A_MOMENT));
      if (scenario === INFERRED) return responseFrom(madeWithAnInferredVibe);
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

function show(
  create: ReturnType<typeof creating>["create"],
  spec = sentSpec,
  specHash: string | null = "hash-one",
  /** What becomes of the page as the panel opens, where a test makes the call the look does not. */
  opens?: WhatItOpens,
) {
  const user = userEvent.setup({ delay: null });
  const panel = (nextSpec = spec, nextHash = specHash) => (
    <SharePanel
      spec={nextSpec}
      specHash={nextHash}
      meta={meta}
      areas={areas}
      create={create}
      {...(opens === undefined ? {} : { opens })}
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
    // It says what follows from what, in a sentence that is joined to the one before it, and
    // nothing that has to be read twice.
    expect(SHARE.noneReplaced).toMatch(/\. Because of that, Burro did not need to replace any of them\.$/);
    expect(SHARE.noneReplaced.split(". ")).toHaveLength(2);
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

describe("the panel, as the look draws it", () => {
  const CSS = readFileSync(path.join(__dirname, "SharePanel.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
  const ALL = rulesOf(CSS);
  const STYLES = ALL.filter((rule) => !/forced-colors/.test(rule.under ?? ""));
  const setsOf = (selector: string) =>
    new Map(STYLES.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) => [...rule.sets]));
  const panel = () => screen.getByRole("region", { name: SHARE.holds.title });
  /** What a button is drawn as: the kind its face bears. */
  const drawnAs = (button: HTMLElement) => button.querySelector("[data-kind]")?.getAttribute("data-kind");
  /** The settings the link holds, as the panel lists them. */
  const stored = () =>
    within(screen.getByRole("heading", { name: SHARE.stored }).nextElementSibling as HTMLElement).getAllByRole("listitem");

  test("test_the_panel_is_a_box_of_the_look_with_what_it_is_called_on_a_band_at_its_head", async () => {
    await opened();

    expect(panel()).toHaveAttribute("data-kind", "box");
    expect(panel().tagName).toBe("SECTION");
    expect(panel().firstElementChild).toBe(screen.getByRole("heading", { level: 3, name: SHARE.holds.title }));
    const band = setsOf(".title");
    expect([band.get("background"), band.get("color"), band.get("font")]).toEqual([
      "var(--ink)",
      "var(--page)",
      "400 var(--name-1) / 1.1 var(--font-name)",
    ]);
    // The box brings its own ground and its own shadow: the sheet lays neither, and cuts nothing off.
    const box = setsOf(".panel");
    expect(["background", "border", "box-shadow", "overflow"].filter((property) => box.has(property))).toEqual([]);
  });

  test("test_the_button_that_makes_the_link_is_the_one_that_matters_most_and_the_one_that_copies_is_not", async () => {
    const { user } = await opened();

    expect(drawnAs(screen.getByRole("button", { name: SHARE.make }))).toBe("go");
    await make(user);

    expect(drawnAs(screen.getByRole("button", { name: SHARE.makeAgain }))).toBe("go");
    expect(drawnAs(screen.getByRole("button", { name: SHARE.copy }))).toBe("plain");
    for (const name of [SHARE.makeAgain, SHARE.copy]) {
      expect(screen.getByRole("button", { name })).toHaveClass("press", "target");
      // Neither holds a state: neither says that it is pressed.
      expect(screen.getByRole("button", { name })).not.toHaveAttribute("aria-pressed");
    }
    expect(panel().querySelectorAll("[data-kind='go']")).toHaveLength(1);
  });

  test("test_the_settings_a_link_holds_are_drawn_as_the_chips_of_a_search_are_each_with_its_thing", async () => {
    const { user } = await opened(INFERRED);
    await make(user);
    const held = madeWithAnInferredVibe.body.data;
    const chips = chipsOf(held.spec, meta, areas, namesOf(held.places), {});

    expect(stored()).toHaveLength(chips.length);
    for (const [at, item] of stored().entries()) {
      const chip = chips[at];
      if (!chip) throw new Error("a setting is listed that the link does not hold");
      const label = item.firstElementChild as HTMLElement;
      const thing = thingOf(chip, meta);
      // Its thing is chosen as the row of chips chooses it, by what the service gives, and is dress.
      expect([chip.key, label.getAttribute("data-kind"), label.getAttribute("data-state")]).toEqual([
        chip.key,
        thing.kind,
        stateOf(chip, held.spec),
      ]);
      const drawing = item.querySelector<HTMLElement>("[aria-hidden='true'] > span, [aria-hidden='true']");
      expect(item.querySelector("[aria-hidden='true']")).not.toBeNull();
      expect(item.innerHTML).toContain(`/art/${drawingOf(thing)}`);
      expect(drawing?.textContent).toBe("");
    }
    // Both what a person said and what nobody said are in the share, so both are held.
    expect(new Set(stored().map((item) => item.firstElementChild?.getAttribute("data-state")))).toEqual(
      new Set(["said", "assumed"]),
    );
  });

  test("test_the_usual_settings_nobody_chose_are_not_counted_among_what_the_link_holds", async () => {
    // The founder, of the same chip over the results: "Unsure what unusal settings:6 assumed
    // refers to. either show those or remove the section." A usual setting that nobody chose
    // moves no area, so the count of them told a person nothing of what they share.
    const { user } = await opened("share-made");
    await make(user);
    const held = made.body.data.spec.weights.filter((weight) => weight.provenance === "default");

    expect(held.length).toBeGreaterThan(0);
    expect(stored().map((item) => item.textContent).filter((said) => /usual settings/i.test(said ?? ""))).toEqual([]);
    expect(stored().length).toBeGreaterThan(3);
  });

  test("test_a_setting_a_link_holds_is_read_and_is_never_pressed", async () => {
    const { user } = await opened("share-made");
    await make(user);

    for (const item of stored()) {
      expect(item.querySelector("button, a, input, [tabindex], [role='button']")).toBeNull();
    }
  });

  test("test_what_nobody_chose_is_said_once_in_words_and_never_by_its_edge_alone", async () => {
    const { user } = await opened(INFERRED);
    await make(user);

    const assumed = stored().filter((item) => item.getAttribute("data-assumed") === "true");

    expect(assumed.length).toBeGreaterThan(0);
    for (const item of assumed) {
      // The kit would say the state after the words. The words say it already, so it is said once.
      expect(item.textContent?.split(CHIPS.assumed).length).toBeGreaterThanOrEqual(2);
      expect(item.querySelectorAll(".state")).toHaveLength(0);
    }
    for (const item of stored().filter((one) => one.getAttribute("data-assumed") !== "true")) {
      expect(item.textContent?.includes(CHIPS.assumed)).toBe(false);
    }
  });

  test("test_the_tick_is_the_browsers_own_checkbox_drawn_as_a_square_that_is_amber_while_it_is_ticked", async () => {
    await opened();
    const tick = screen.getByRole("checkbox", { name: SHARE.exact.label });

    expect(tick.tagName).toBe("INPUT");
    expect(tick).toHaveAttribute("type", "checkbox");
    expect(tick).toHaveClass("target-min");
    const square = setsOf(".check > input");
    // Twelve art pixels square is 24 pixels of a phone: the smallest a small control may be.
    expect([square.get("width"), square.get("height"), square.get("appearance")]).toEqual([
      "calc(var(--px) * 12)",
      "calc(var(--px) * 12)",
      "none",
    ]);
    expect(square.get("border")).toBe("var(--px) solid var(--ink)");
    expect(setsOf(".check > input:checked").get("background")?.trim().endsWith("var(--chosen)")).toBe(true);
    // Where the system draws in colours of its own the tick is the browser's own, ticked or not.
    const forced = ALL.filter((rule) => /forced-colors/.test(rule.under ?? "") && /^\.check > input/.test(rule.selector));
    expect(forced.map((rule) => [rule.selector, rule.sets.get("appearance")])).toEqual([
      [".check > input", "auto"],
      [".check > input:checked", "auto"],
    ]);
  });

  test("test_the_field_that_holds_the_link_is_sunk_into_the_page_and_weighs_more_than_what_is_said_of_every_field", () => {
    const field = STYLES.filter((rule) => rule.sets.has("box-shadow") && /\.field$/.test(rule.selector));

    expect(field.map((rule) => [rule.selector, rule.sets.get("box-shadow")])).toEqual([
      [".linkRow > .field", "inset var(--px) var(--px) 0 var(--sand)"],
    ]);
    expect(heavier(weightOf(".linkRow > .field"), weightOf("input:not([type=\"checkbox\"], [type=\"radio\"], [type=\"range\"])"))).toBe(true);
    // A link is read exactly, in the face an id is set in, which is the face of a sentence.
    expect(field[0]?.sets.get("font-family")).toBe("var(--font-mono)");
  });

  test("test_a_link_that_could_not_be_made_is_cream_with_a_band_of_poppy_and_its_words_in_ink", async () => {
    const { user } = await opened("error-internal");
    await make(user);

    expect(screen.getByRole("alert")).toHaveClass("error");
    const sets = setsOf(".error");
    expect([sets.get("background"), sets.get("border"), sets.get("color"), sets.get("box-shadow")]).toEqual([
      "var(--bg)",
      "var(--edge) solid var(--border)",
      "var(--text)",
      "inset var(--band) 0 0 var(--error-edge)",
    ]);
    expect(setsOf(".errorTitle").get("color")).toBe("var(--error)");
    expect(STYLES.filter((rule) => rule.sets.get("color") === "var(--error-edge)").map((rule) => rule.selector)).toEqual([]);
  });

  test("test_every_colour_a_face_and_a_size_is_a_token_and_nothing_is_dimmed_or_moves", () => {
    expect(CSS.match(/#[0-9a-f]{3,8}\b|\b(rgb|hsl|oklch|lab|lch)a?\(/gi) ?? []).toEqual([]);
    expect(CSS.match(/url\([^)]*\)/g) ?? []).toEqual([]);
    const faces = STYLES.flatMap((rule) =>
      [...rule.sets].filter(([property]) => property === "font" || property === "font-family").map(([, value]) => value),
    );
    expect(faces.length).toBeGreaterThan(2);
    expect(faces.filter((face) => !/var\(--font-(say|name|mono)\)$/.test(face))).toEqual([]);
    const moving = ALL.filter((rule) =>
      [...rule.sets.keys()].some((property) => /^(animation|transition|transform|translate|rotate|scale|zoom|opacity|filter)/.test(property)),
    );
    expect(moving.map((rule) => rule.selector)).toEqual([]);
    expect(ALL.filter((rule) => /:(hover|focus|focus-within|focus-visible|active)\b/.test(rule.selector)).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_nothing_that_holds_words_has_a_height_of_its_own_so_that_text_can_be_made_larger", () => {
    const fixed = ALL.filter((rule) =>
      [...rule.sets.keys()].some((property) => /^(height|max-height|block-size|max-block-size)$/.test(property)),
    );

    // The square of the tick is drawn in art pixels. Nothing that is read has a height.
    expect(fixed.map((rule) => rule.selector)).toEqual([".check > input"]);
  });
});

describe("the panel, opened where its button stands at the foot of the window", () => {
  /** The button stands from 788 to 832 of a window 844 high, and what it opens from 848 to 1,522. */
  function atTheFoot() {
    const measure = jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (
      this: HTMLElement,
    ) {
      const [top, foot] = this.tagName === "BUTTON" ? [788, 832] : [848, 1522];
      return { top, bottom: foot, left: 0, right: 0, x: 0, y: top, width: 0, height: foot - top, toJSON: () => ({}) };
    });
    const high = window.innerHeight;
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 844 });
    const moved: number[] = [];
    const scroll = jest.spyOn(window, "scrollBy").mockImplementation(((_: number, by: number) => void moved.push(by)) as typeof window.scrollBy);
    const restore = () => {
      scroll.mockRestore();
      measure.mockRestore();
      Object.defineProperty(window, "innerHeight", { configurable: true, value: high });
    };
    return { moved, restore };
  }

  test("test_what_is_pressed_stays_under_the_hand_and_the_page_is_not_moved", async () => {
    // Seen in a browser, walked by pointer: pressed where it stood at the foot of the window,
    // the button went 616 px up a phone and 514 up a desk, and something else lay under the
    // pointer. The founder's rule, which holds whatever is built: nothing moves under a press.
    const { moved, restore } = atTheFoot();
    try {
      const { user } = show(creating().create);

      await user.click(screen.getByRole("button", { name: SHARE.open }));

      expect(WHAT_IT_OPENS).toBe("held");
      expect(screen.getByRole("region", { name: SHARE.holds.title })).toBeInTheDocument();
      expect(moved).toEqual([]);
      // It says that it is open, and what it opened follows it in the page.
      expect(screen.getByRole("button", { name: SHARE.open })).toHaveAttribute("aria-expanded", "true");
      expect(screen.getByRole("button", { name: SHARE.open })).toHaveFocus();
    } finally {
      restore();
    }
  });

  test("test_one_line_of_the_look_brings_what_it_opens_into_sight_as_it_did", async () => {
    // Seen in a browser, before: pressed at 788 of 844, it opened its panel from 848: the
    // button turned amber, and nothing else was seen to happen. Both cannot be kept.
    const { moved, restore } = atTheFoot();
    try {
      const { user } = show(creating().create, sentSpec, "hash-one", "brought");

      await user.click(screen.getByRole("button", { name: SHARE.open }));

      expect(WHAT_IT_OPENS_MAY_BE).toEqual(["held", "brought"]);
      // The page is moved as far as brings the head of the panel into sight, and no further:
      // a press lands where it was aimed, so the page goes by no more than it must. The rest
      // of the panel is the person's to scroll to.
      expect(screen.getByRole("region", { name: SHARE.holds.title })).toBeInTheDocument();
      expect(moved).toEqual([848 + HEAD - 844]);
      // What was pressed is never taken over the top of the window: it stood at 788.
      expect(moved.every((by) => by > 0 && by <= 788)).toBe(true);
      expect(screen.getByRole("button", { name: SHARE.open })).toHaveFocus();
    } finally {
      restore();
    }
  });
});
