import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { FEATURES, SETTINGS } from "@/content/settings";
import { USUAL } from "@/content/usual";
import { failed } from "@/lib/api/failure";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Operations, PreferenceSpec } from "@/lib/api/schema";
import { edits } from "@/lib/search/edits";

import { faultsIn } from "../../../test/support/axe";
import { groupsOf } from "./groups";
import { NAMED_IN_SIGHT, SAYS_AT_THEIR_HEAD } from "./look";
import { SettingsPanel } from "./SettingsPanel";

const meta = recordedAnswer("get_meta", "meta").body.data;
/**
 * What the service calls each family of vibes, by the id of the family. A name is the
 * service's to write, and it has written two again: so a test finds a group by the name
 * the service gives it, and writes none down.
 */
const familyCalled = (id: string) => meta.families.find((one) => one.family === id)?.label ?? id;
const GREEN = familyCalled("green");
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
/** "Renting a 1 bed for about £1,700 a month, leafy and quiet, 35 minutes to Cindermoor Works", as it was ranked. */
const first = recordedAnswer("rank", "rank-first").body.data.spec;
const NAMED = { "syn-p0021": "Cindermoor Works" } as const;

/** What a search starts from, as a search that is open holds it: nothing in it was asked for. */
const nothingAsked: PreferenceSpec = { ...meta.defaults.rent };
/** What Burro counts in every search, of renting, by the names the API gives, in the order of the groups. */
const SIX = groupsOf(meta.defaults.rent, meta, areas, NAMED).flatMap((group) => group.usual);

interface Shown {
  readonly spec: PreferenceSpec;
  readonly version?: number;
  /** Whether a search is open, as the page says it. Left out, the settings tell it from the spec. */
  readonly begun?: boolean;
  readonly standing?: boolean;
  /** Told of every edit a control of the settings sends. */
  readonly sent?: Operations[];
}

function Settings({ spec, version = 1, begun, standing = true, sent }: Shown) {
  return (
    <SettingsPanel
      spec={spec}
      meta={meta}
      areas={areas}
      placeNames={NAMED}
      onEdit={(operations) => sent?.push(operations)}
      onTenure={() => undefined}
      searchPlaces={() => Promise.resolve(failed("offline"))}
      onAddPlace={() => undefined}
      version={version}
      open
      onToggle={() => undefined}
      standing={standing}
      begun={begun}
    />
  );
}

/** Where the settings stand: before a search, in Deep search, and once one is open, under "Refine search". */
const STAND = [
  { where: "before a search", spec: meta.defaults.rent },
  { where: "once a search is open", spec: first },
] as const;

const settings = () => screen.getByRole("region", { name: SETTINGS.title });
/** Every sentence at the head of the settings, over their groups, in the order they stand. */
const head = () => [...settings().querySelectorAll(":scope > p")].map((line) => line.textContent);
const bars = () => [...document.querySelectorAll<HTMLElement>("button[data-arrow][data-rest]")];
const standOpen = () =>
  bars()
    .filter((bar) => bar.getAttribute("aria-expanded") === "true")
    .map((bar) => bar.querySelector(".name")?.textContent);

describe("the head of the settings", () => {
  test("test_a_search_starts_from_six_settings_that_nobody_chose", () => {
    expect(SIX).toHaveLength(6);
    expect(new Set(SIX)).toEqual(
      new Set(["Cleaner air", "Nearer a town centre", "Less transport noise", "Nearer a park", "More lines nearby", "Nearer a station"]),
    );
  });

  test("test_the_settings_are_named_space_requirements_which_is_the_name_the_founder_gave_them", () => {
    // The founder, of the settings of Deep search: "rename it to Space requirements".
    expect(SETTINGS.title).toBe("Space requirements");
    expect(NAMED_IN_SIGHT).toBe("always");
  });

  test.each(STAND)("test_their_name_stands_over_them_as_a_heading_and_they_are_found_by_it: $where", ({ spec }) => {
    render(<Settings spec={spec} />);

    expect(within(settings()).getByRole("heading", { level: 2, name: SETTINGS.title })).toBeVisible();
    expect(within(settings()).getAllByRole("heading")).toHaveLength(1);
    // Whoever hears the page finds them by their name, as every test of the page does.
    expect(settings().tagName).toBe("SECTION");
    expect(settings()).toHaveAccessibleName(SETTINGS.title);
    expect(screen.queryByText("Settings")).toBeNull();
  });

  test.each(STAND)("test_no_sentence_stands_at_their_head_for_the_tab_says_what_deep_search_is_once: $where", ({ spec }) => {
    // The founder: "on deep search you have duplicated the explainer text, remove the
    // explainer copy from the settings section". Their name, and then their groups.
    render(<Settings spec={spec} />);

    expect(SAYS_AT_THEIR_HEAD).toBe("nothing");
    expect(head()).toEqual([]);
    expect([...settings().children].map((part) => part.tagName)).toEqual(["H2", "DIV"]);
    expect(settings().lastElementChild).toBe(document.querySelector(".stack"));
    // Neither what was said before a search nor what was said once one was open.
    const said = settings().textContent ?? "";
    expect(/in the groups below|straight away|do the same job as typing|into account in every search/.test(said)).toBe(false);
    for (const say of [USUAL.before, USUAL.little, USUAL.also, USUAL.alone]) expect(said.includes(say(SIX))).toBe(false);
  });

  test("test_behind_their_own_button_the_button_names_them_and_nothing_stands_over_their_groups", () => {
    // The button says their name, and what it opens says it no second time.
    render(<Settings spec={first} standing={false} />);
    const box = document.querySelector("[data-kind='box']") as HTMLElement;

    expect(screen.getByRole("button", { name: SETTINGS.title })).toHaveAttribute("aria-expanded", "true");
    expect(within(box).queryAllByRole("heading")).toEqual([]);
    expect([...box.children].map((part) => part.className)).toEqual(["stack"]);
  });

  test("test_what_burro_counts_in_every_search_is_named_on_the_bar_of_its_group_so_that_it_can_be_found", () => {
    // A result said "Based on 9 of the 10 things that count in your search" of a search of
    // four things. No sentence names the other six now: the bar of the group of each does.
    render(<Settings spec={first} />);
    const onTheBars = bars().map((bar) => bar.querySelector(".holds")?.textContent ?? "");

    for (const name of SIX) {
      expect([name, onTheBars.filter((holds) => holds.includes(name))]).toEqual([
        name,
        [expect.stringContaining("Counted in every search: ")],
      ]);
    }
  });

  test("test_with_every_state_of_their_head_the_settings_have_no_accessibility_fault", async () => {
    for (const spec of [meta.defaults.rent, first, nothingAsked]) {
      const { container, unmount } = render(<Settings spec={spec} />);
      expect(await faultsIn(container)).toEqual([]);
      unmount();
    }
  });
});

describe("whether a search is open, where the page says", () => {
  test("test_left_out_it_is_told_from_the_spec_as_it_was", () => {
    // Before a search a couple of groups stand open to show that a group folds. Once one
    // is open none does: it is by what stands open that the two are told apart here.
    const { unmount } = render(<Settings spec={meta.defaults.buy} />);
    expect(standOpen()).toEqual([SETTINGS.money, SETTINGS.journeys]);
    unmount();

    render(<Settings spec={nothingAsked} />);
    expect(standOpen()).toEqual([]);
  });

  test("test_the_settings_gather_what_is_chosen_before_a_search_though_the_spec_is_one_the_api_returned", () => {
    // In Deep search nothing is ranked until its button is pressed. What was chosen there
    // is in the search the page holds, and no search is open.
    const chosen: PreferenceSpec = { ...meta.defaults.rent, tags: [{ tag_id: "leafy", weight: 0.7, toward: "high", provenance: "ui_edit" }] };
    render(<Settings spec={chosen} begun={false} />);

    expect(within(settings()).getByRole("heading", { level: 2, name: SETTINGS.title })).toBeVisible();
    // A couple of groups stand open, as before any search, and the bar says what was chosen.
    expect(standOpen()).toEqual([SETTINGS.money, SETTINGS.journeys]);
    expect(screen.getByRole("button", { name: GREEN }).querySelector(".holds")?.textContent).toBe(
      "Leafy. Counted in every search: Nearer a park",
    );
  });

  test("test_the_page_may_say_that_a_search_is_open_which_holds_what_a_search_starts_from", () => {
    // A person pressed the button with nothing chosen, and the ranking is on its way.
    render(<Settings spec={meta.defaults.rent} begun />);

    expect(head()).toEqual([]);
    expect(standOpen()).toEqual([]);
  });

  test("test_as_a_search_opens_of_the_pages_button_the_groups_that_stood_open_to_show_are_closed_and_what_a_person_opened_is_not", async () => {
    const chosen: PreferenceSpec = { ...meta.defaults.rent, tags: [{ tag_id: "leafy", weight: 0.7, toward: "high", provenance: "ui_edit" }] };
    const { rerender } = render(<Settings spec={chosen} begun={false} />);
    await userEvent.setup({ delay: null }).click(screen.getByRole("button", { name: GREEN }));
    expect(standOpen()).toEqual([SETTINGS.money, SETTINGS.journeys, GREEN]);
    // The button that ranks is the page's, and stands outside the groups: the hand is on it.
    screen.getByRole("button", { name: GREEN }).blur();

    rerender(<Settings spec={chosen} begun />);

    expect(standOpen()).toEqual([GREEN]);
  });

  test("test_as_a_search_opens_of_a_setting_that_was_moved_no_group_closes_under_the_hand", () => {
    // The other way of the page, where a setting that is moved ranks at once: the person is in the settings.
    const { rerender } = render(<Settings spec={meta.defaults.rent} begun={false} />);
    screen.getByRole("radio", { name: "Buying" }).focus();

    rerender(<Settings spec={{ ...meta.defaults.buy }} begun version={2} />);

    expect(standOpen()).toEqual([SETTINGS.money, SETTINGS.journeys]);
  });
});

describe("what nobody chose can be changed where it is named", () => {
  const user = () => userEvent.setup({ delay: null });
  const bar = (name: string) => screen.getByRole("button", { name });
  /** What a bar opened: the part of the page it says it shows. */
  const openedBy = (name: string) => document.getElementById(bar(name).getAttribute("aria-controls") ?? "") as HTMLElement;

  test("test_what_the_bar_of_a_group_names_is_in_sight_as_the_group_opens", async () => {
    // Seen in a browser: the bar of Green said "Counted in every search: Nearer a park", and
    // the group opened onto two vibes and a river. Nearer a park is a measurement that goes
    // into a vibe, and its switch stood only in what the vibe is made of, which was closed.
    render(<Settings spec={first} />);
    const press = user();

    await press.click(bar(GREEN));

    expect(bar(FEATURES.madeOfName("Parks close by"))).toHaveAttribute("aria-expanded", "true");
    expect(within(openedBy(FEATURES.madeOfName("Parks close by"))).getByRole("switch", { name: "Nearer a park" })).toBeChecked();
    // A vibe that holds nothing of the kind is closed, as it was.
    expect(bar(FEATURES.madeOfName("Leafy"))).toHaveAttribute("aria-expanded", "false");
  });

  test("test_every_name_a_bar_gives_has_a_switch_in_sight_in_the_group_whose_bar_names_it_and_each_is_there_once", async () => {
    for (const spec of [first, meta.defaults.rent, meta.defaults.buy]) {
      const { unmount } = render(<Settings spec={spec} />);
      const press = user();
      const named = groupsOf(spec, meta, areas, NAMED).filter((group) => group.usual.length > 0);

      expect(named.flatMap((group) => group.usual).length).toBeGreaterThanOrEqual(6);
      for (const group of named) {
        if (bar(group.label).getAttribute("aria-expanded") !== "true") await press.click(bar(group.label));
        for (const name of group.usual) {
          // Once, and in nothing that is closed: what is closed is not on the page.
          const found = within(openedBy(group.label)).getAllByRole("switch", { name });
          expect([group.label, name, found.length]).toEqual([group.label, name, 1]);
          expect(found[0]).toBeChecked();
        }
        await press.click(bar(group.label));
      }
      unmount();
    }
  });

  test("test_it_is_turned_off_there_by_the_edit_any_switch_sends", async () => {
    const sent: Operations[] = [];
    render(<Settings spec={first} sent={sent} />);
    const press = user();
    await press.click(bar(GREEN));

    await press.click(screen.getByRole("switch", { name: "Nearer a park" }));

    expect(sent).toEqual([edits.featureOff("park_proximity")]);
  });

  test("test_once_a_person_has_changed_it_it_stays_where_it_stood_though_it_is_theirs_now", async () => {
    // What is moved must not go from under the hand: changed, it is no longer what nobody chose.
    const park = first.weights.find((weight) => weight.feature_id === "park_proximity");
    const as = (weight: number): PreferenceSpec => ({
      ...first,
      weights: first.weights.map((one) => (one === park ? { ...one, weight, provenance: "ui_edit" as const } : one)),
    });
    const { rerender } = render(<Settings spec={first} />);
    await user().click(bar(GREEN));
    screen.getByRole("switch", { name: "Nearer a park" }).focus();

    rerender(<Settings spec={as(0.6)} version={2} />);
    expect(screen.getByRole("switch", { name: "Nearer a park" })).toBeChecked();
    // And taken off, it is still there to be put back, when the search changes elsewhere too.
    screen.getByRole("button", { name: GREEN }).focus();
    rerender(<Settings spec={as(0)} version={3} />);
    expect(screen.getByRole("switch", { name: "Nearer a park" })).not.toBeChecked();
    expect(bar(GREEN).querySelector(".holds")?.textContent).toBe("Leafy. Not counted: Nearer a park");
  });

  test("test_what_a_vibe_is_made_of_is_closed_where_the_search_holds_no_part_of_it_by_itself", async () => {
    // A release holds a hundred measurements, and a person came for a few of them.
    const bare: PreferenceSpec = { ...first, weights: first.weights.filter((weight) => weight.feature_id !== "park_proximity") };
    render(<Settings spec={bare} />);
    await user().click(bar(GREEN));

    expect(bar(FEATURES.madeOfName("Parks close by"))).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("switch", { name: "Nearer a park" })).toBeNull();
  });
});
