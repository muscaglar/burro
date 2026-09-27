/**
 * What the page keeps of what a person did that is no part of a search: which
 * of the two ways in is chosen, and which helper and which groups of the
 * settings are open. docs/design/web.md, section 10: each is kept by the page,
 * in memory, while it is open, and is in no address, in nothing the browser
 * keeps, in no line of the console and in no request.
 *
 * Whether the rabbit was stopped was kept so too. The button that stopped him
 * is gone, by the founder's second review, and what held it here with it:
 * nothing of him is kept, since nothing of him can be chosen.
 *
 * And what was typed is kept while the other way in is chosen: in the box it
 * was typed in, and nowhere else.
 *
 * Each test plants a canary, a string found nowhere else, in what is typed,
 * and watches everywhere it must not be found.
 */

import { act, cleanup, screen, within } from "@testing-library/react";

import { HELPERS } from "@/content/helpers";
import { FIND_AREA, PLACE, SHELF, TENURE_CHOICE } from "@/content/search";
import { SETTINGS } from "@/content/settings";
import { WAYS } from "@/content/ways";

import { BASE, setOnline } from "../support/api";
import {
  arrived,
  CANARY,
  firstSearch,
  helper,
  helpers,
  meta,
  openSearch,
  panelOf,
  promptBox,
  search,
  settingsAt,
  settled,
  tabOf,
  theSettings,
  way,
  whatRefines,
} from "../support/search";
import { watch, type Watch } from "../support/watch";

jest.mock("next/navigation", () => ({ usePathname: () => "/" }));

const TYPED = `leafy and quiet, 30 minutes to ${CANARY}`;

beforeEach(() => setOnline(true));

/** Runs what a person does under a watch, and answers with what the watch saw. */
async function watched<Done>(does: (watching: Watch) => Promise<Done>): Promise<Done> {
  const watching = watch();
  try {
    return await does(watching);
  } finally {
    watching.stop();
  }
}

/** Every attribute of the page, as written: no word that was typed may be in one. */
const attributes = () =>
  [...document.querySelectorAll("*")].flatMap((element) => [...element.attributes].map((attribute) => `${attribute.name}=${attribute.value}`));
/** The markup of the page, which holds what a field holds only where it was written into it. */
const markup = () => document.documentElement.innerHTML;
const listOf = (field: HTMLElement) => document.getElementById(field.getAttribute("aria-controls") ?? "") as HTMLElement;
const barOf = (group: string) => within(theSettings()).getByRole("button", { name: group });

/** What a watch saw and what the page holds, each as a yes or a no: a test that fails must not print what was typed. */
const found = (watching: Watch, at: string) => ({
  kept: watching.storage.length,
  history: watching.history.length,
  console: watching.console.length,
  address: window.location.href === at,
  title: document.title,
  typedInAnAddress: watching.addresses().includes(CANARY),
  typedOutsideThePage: watching.everythingOutsideThePage().includes(CANARY),
  typedInTheMarkup: markup().includes(CANARY),
  typedInAnAttribute: attributes().some((attribute) => attribute.includes(CANARY)),
});
const NOTHING = (at: string) => ({
  kept: 0,
  history: 0,
  console: 0,
  address: window.location.href === at,
  title: "",
  typedInAnAddress: false,
  typedOutsideThePage: false,
  typedInTheMarkup: false,
  typedInAnAttribute: false,
});

describe("what was typed, while the other way in is chosen", () => {
  test("test_changing_way_keeps_what_was_typed_in_the_box_it_was_typed_in", async () => {
    const { user } = await openSearch();
    const box = promptBox();
    await user.type(box, TYPED);

    // By a pointer, and back by a key, and again the other way about.
    await user.click(tabOf("deep"));
    expect([panelOf("quick").contains(box), box.value === TYPED, box.isConnected]).toEqual([true, true, true]);
    await user.keyboard("{ArrowLeft}");
    expect([promptBox() === box, box.value === TYPED]).toEqual([true, true]);
    act(() => tabOf("quick").focus());
    await user.keyboard("{End}");
    await user.click(tabOf("quick"));

    expect([promptBox() === box, box.value === TYPED]).toEqual([true, true]);
    // It can be gone on with where it was left, and sent.
    await user.type(promptBox(), ", renting");
    expect(promptBox().value === `${TYPED}, renting`).toBe(true);
  });

  test("test_it_is_nowhere_on_the_page_but_in_the_box_whichever_way_is_chosen", async () => {
    const { user } = await openSearch();
    await user.type(promptBox(), TYPED);

    for (const chosen of ["deep", "quick", "deep"] as const) {
      await way(user, chosen);
      // The markup of the page holds no word of it, and nor does any attribute: the box
      // holds it as a field holds what is typed, and not as words written into the page.
      expect([chosen, markup().includes(CANARY)]).toEqual([chosen, false]);
      expect([chosen, attributes().filter((attribute) => attribute.includes(CANARY)).length]).toEqual([chosen, 0]);
      expect([chosen, document.body.textContent?.includes(CANARY)]).toEqual([chosen, false]);
    }
    // Nor does the page say how long it is, or where it ends: no count of it is written down.
    expect(attributes().filter((attribute) => attribute.endsWith(`=${TYPED.length}`))).toEqual([]);
  });

  test("test_it_is_in_no_address_and_in_nothing_the_browser_keeps_however_the_way_is_changed", async () => {
    await watched(async (watching) => {
      const { user, api } = await openSearch();
      const at = window.location.href;
      const sent = api.calls.length;
      await user.type(promptBox(), TYPED);

      await user.click(tabOf("deep"));
      await user.keyboard("{ArrowRight}{ArrowLeft}{Home}{End}");
      await user.click(tabOf("quick"));
      await user.click(tabOf("deep"));
      await way(user, "quick");

      expect(found(watching, at)).toEqual(NOTHING(at));
      // Which way is chosen is said by the tab, and by nothing a link or an address could carry.
      expect(watching.addresses()).not.toMatch(/quick|deep/i);
      // To choose a way asks nothing of the service, with words in the box or without.
      expect(api.calls).toHaveLength(sent);
    });
  });

  test("test_what_is_typed_in_the_fields_of_the_second_way_goes_in_the_body_of_the_search_for_places_and_nowhere_else", async () => {
    await watched(async (watching) => {
      const { user, api } = await openSearch(firstSearch());
      const at = window.location.href;
      await user.type(promptBox(), TYPED);
      await way(user, "deep");
      // Two fields find by name there: the one of the journeys, among the settings, which
      // finds a place to reach, and the one at the foot, which finds an area.
      const fields = () => [
        within(theSettings()).getByRole<HTMLInputElement>("combobox", { name: PLACE.label }),
        within(panelOf("deep")).getByRole<HTMLInputElement>("textbox", { name: FIND_AREA.labelAlone }),
      ];

      const [place, area] = fields();
      await user.type(place as HTMLElement, `${CANARY} wor`);
      await within(listOf(place as HTMLElement)).findAllByRole("option");
      await user.keyboard("{Escape}");
      // An area that is found is a link to its page, and no option of a list.
      await user.type(area as HTMLElement, `${CANARY} wor`);
      await screen.findByRole("group", { name: FIND_AREA.title });
      await user.keyboard("{Escape}");
      await way(user, "quick");
      await way(user, "deep");
      await arrived();

      // Each field holds what was typed in it still, and the box what was typed in the box.
      for (const field of fields()) {
        expect(field.getAttribute("value") ?? "").toBe("");
        expect(field.value === `${CANARY} wor`).toBe(true);
      }
      expect(found(watching, at)).toEqual(NOTHING(at));
      // What was typed in the field was sent to find a place, in the body of a post, as `q`.
      // What was typed in the box was sent nowhere: nothing has been asked for yet.
      const holding = api.calls.filter((call) => JSON.stringify([call.url, call.sent, call.init.headers]).includes(CANARY));
      expect(holding.length).toBeGreaterThan(0);
      expect(new Set(holding.map((call) => `${call.method} ${call.path}`))).toEqual(new Set(["POST /v1/places/search"]));
      for (const call of holding) {
        expect(call.url).toBe(`${BASE}${call.path}`);
        expect(call.init).toMatchObject({ method: "POST", credentials: "omit", referrerPolicy: "no-referrer", cache: "no-store" });
        const body = call.body as Record<string, unknown>;
        expect(Object.keys(body).filter((key) => JSON.stringify(body[key]).includes(CANARY))).toEqual(["q"]);
        expect(call.sent?.includes("leafy")).toBe(false);
      }
      expect(api.callsTo("interpret")).toEqual([]);
      expect(api.callsTo("rank")).toEqual([]);
    });
  });

  test("test_a_search_that_opens_of_the_second_way_sends_no_word_of_what_stands_in_the_box", async () => {
    // The box is on the page while the second way is chosen, with what was typed in it. The
    // button that ranks the settings sends the settings, and the words are not read by it.
    await watched(async (watching) => {
      const { user, api } = await openSearch(firstSearch().on("rank", "rank-default-rent"));
      const at = window.location.href;
      await user.type(promptBox(), TYPED);
      await way(user, "deep");

      await user.click(within(panelOf("deep")).getByRole("button", { name: SETTINGS.rank }));
      await settled();

      expect(api.callsTo("rank").length).toBeGreaterThan(0);
      expect(api.callsTo("interpret")).toEqual([]);
      expect(api.calls.filter((call) => `${call.url} ${call.sent ?? ""}`.includes(CANARY))).toEqual([]);
      expect(found(watching, at)).toEqual(NOTHING(at));
      // The words are in the box still, for the person to send or to take out.
      expect(promptBox().value === TYPED).toBe(true);
    });
  });
});

describe("which way is chosen, and which helper is open", () => {
  test("test_choosing_a_way_and_opening_a_helper_keep_nothing_in_the_browser_and_ask_nothing_of_the_service", async () => {
    await watched(async (watching) => {
      const { user, api } = await openSearch();
      const at = window.location.href;
      const sent = api.calls.length;

      await helper(user, "example");
      await helper(user, "word");
      await user.click(within(screen.getByRole("region", { name: SHELF.title })).getAllByRole("button")[0] as HTMLElement);
      await way(user, "deep");
      await way(user, "quick");
      await user.keyboard("{Escape}");

      expect(found(watching, at)).toEqual(NOTHING(at));
      expect(watching.addresses()).not.toMatch(/quick|deep|example|shelf/i);
      expect(api.calls).toHaveLength(sent);
    });
  });

  test("test_a_page_that_is_opened_again_begins_as_a_page_first_stands_and_holds_nothing_of_the_last", async () => {
    const first = await openSearch();
    await first.user.type(promptBox(), TYPED);
    await helper(first.user, "example");
    await settingsAt(first.user, SETTINGS.airAndNoise);
    // Renting or buying is asked where the money is, which stands open: so it is chosen
    // before that group is closed.
    await first.user.click(within(panelOf("deep")).getAllByRole("radio", { name: TENURE_CHOICE.buy })[0] as HTMLElement);
    await first.user.click(barOf(SETTINGS.money));
    const field = screen.getByRole("textbox", { name: FIND_AREA.labelAlone });
    await first.user.type(field, "pel");
    await screen.findByRole("group", { name: FIND_AREA.title });

    // The page is closed, and opened again: nothing of the last is handed to the next.
    cleanup();
    const { user } = await openSearch();

    expect(tabOf("quick")).toHaveAttribute("aria-selected", "true");
    expect(promptBox()).toHaveValue("");
    expect(within(helpers()).getAllByRole("button").map((one) => one.getAttribute("aria-expanded"))).toEqual(["false", "false"]);
    expect(markup().includes(CANARY)).toBe(false);
    await way(user, "deep");
    expect(screen.getByRole("textbox", { name: FIND_AREA.labelAlone })).toHaveValue("");
    expect(within(panelOf("deep")).getAllByRole("radio", { name: TENURE_CHOICE.rent })[0]).toBeChecked();
    expect(barOf(SETTINGS.money)).toHaveAttribute("aria-expanded", "true");
    expect(barOf(SETTINGS.journeys)).toHaveAttribute("aria-expanded", "true");
    expect(barOf(SETTINGS.airAndNoise)).toHaveAttribute("aria-expanded", "false");
  });

  test("test_the_names_of_the_ways_and_of_the_helpers_say_nothing_of_a_place_and_hold_no_figure", () => {
    for (const name of [WAYS.label, WAYS.quick, WAYS.deep, HELPERS.label, HELPERS.example, HELPERS.word]) {
      expect([name, /\d/.test(name)]).toEqual([name, false]);
    }
  });
});

describe("which groups of the settings are open", () => {
  test.each([
    { where: "before a search", searched: false },
    { where: "once a search is open", searched: true },
  ])("test_opening_and_closing_them_keeps_nothing_in_the_browser_and_asks_nothing_of_the_service: $where", async ({ searched }) => {
    await watched(async (watching) => {
      const { user, api } = await openSearch();
      const at = window.location.href;
      if (searched) await search(user, TYPED);
      await settingsAt(user);
      const sent = api.calls.length;
      const asked = watching.storage.length + watching.history.length + watching.console.length;

      // Each of five groups is pressed: one that stood open is closed, and one that was
      // closed is opened. Which stand open at first is the settings' to choose, by their look.
      const families = meta.data.families.map((family) => family.label).slice(0, 2);
      const groups = [SETTINGS.money, SETTINGS.journeys, SETTINGS.airAndNoise, ...families];
      const stand = () => groups.map((group) => barOf(group).getAttribute("aria-expanded"));
      const stood = stand();
      for (const group of groups) await user.click(barOf(group));
      const pressed = stand();
      expect(pressed).toEqual(stood.map((open) => (open === "true" ? "false" : "true")));
      expect(pressed).toContain("true");
      if (searched) {
        // The fold over them is closed and opened: what was opened is open again, and what
        // was closed is closed, kept by the page.
        await user.click(whatRefines() as HTMLElement);
        await user.click(whatRefines() as HTMLElement);
        expect(stand()).toEqual(pressed);
      }

      expect(watching.storage.length + watching.history.length + watching.console.length).toBe(asked);
      expect(found(watching, at)).toEqual(NOTHING(at));
      expect(api.calls).toHaveLength(sent);
    });
  });

  test("test_what_names_a_group_in_the_markup_is_of_the_page_and_never_of_what_was_typed_or_of_a_place", async () => {
    await watched(async (watching) => {
      const { user } = await openSearch();
      await search(user, TYPED);
      await settingsAt(user, SETTINGS.money, SETTINGS.journeys, SETTINGS.airAndNoise);

      // A bar names what it opens, and is described by what it holds: both by an id of the page's own.
      const named = within(theSettings())
        .getAllByRole("button")
        .flatMap((bar) => ["aria-controls", "aria-labelledby", "aria-describedby"].flatMap((name) => bar.getAttribute(name) ?? []));
      expect(named.length).toBeGreaterThan(10);
      expect(named.filter((id) => id.includes(CANARY) || /syn-[pn]\d+|\s/.test(id))).toEqual([]);
      expect(watching.ids().includes(CANARY)).toBe(false);
      expect(/syn-p\d+/.test(watching.ids())).toBe(false);
    });
  });
});
