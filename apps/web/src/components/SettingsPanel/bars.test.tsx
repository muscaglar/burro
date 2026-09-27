import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DIMENSION } from "@/content/labels";
import { SETTINGS } from "@/content/settings";
import { USUAL } from "@/content/usual";
import { failed } from "@/lib/api/failure";
import { recordedAnswer } from "@/lib/api/recorded";
import type { PreferenceSpec } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { SettingsPanel } from "./SettingsPanel";

const meta = recordedAnswer("get_meta", "meta").body.data;
/**
 * What the service calls each family of vibes, by the id of the family. A name is the
 * service's to write, and it has written two again: so a test finds a group by the name
 * the service gives it, and writes none down.
 */
const familyCalled = (id: string) => meta.families.find((one) => one.family === id)?.label ?? id;
const [STREETS, GOING_OUT, GREEN, WHO_LIVES_THERE] = [familyCalled("streets_homes"), familyCalled("pace_food"), familyCalled("green"), familyCalled("who_lives_there")];
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
/** "Renting a 1 bed for about £1,700 a month, leafy and quiet, 35 minutes to Cindermoor Works", as it was ranked. */
const ranked = recordedAnswer("rank", "rank-first").body;
const first = ranked.data.spec;
const NAMED = { "syn-p0021": "Cindermoor Works" } as const;

function Settings({ spec, version = 1 }: { spec: PreferenceSpec; version?: number }) {
  return (
    <SettingsPanel
      spec={spec}
      meta={meta}
      areas={areas}
      placeNames={NAMED}
      onEdit={() => undefined}
      onTenure={() => undefined}
      searchPlaces={() => Promise.resolve(failed("offline"))}
      onAddPlace={() => undefined}
      version={version}
      open
      onToggle={() => undefined}
      standing
    />
  );
}

const bars = () => [...document.querySelectorAll<HTMLElement>("button[data-arrow][data-rest]")];
const named = (bar: HTMLElement) => bar.querySelector(".name")?.textContent ?? "";
/** The groups that stand open, by what each is called. */
const standOpen = () => bars().filter((bar) => bar.getAttribute("aria-expanded") === "true").map(named);
const bar = (name: string) => screen.getByRole("button", { name });
const user = () => userEvent.setup({ delay: null });

describe("the groups of the settings, as one stack of bars", () => {
  test("test_every_group_is_a_bar_of_one_stack_and_stands_directly_under_the_one_before_it", () => {
    const { container } = render(<Settings spec={first} />);
    const stack = container.querySelector(".stack") as HTMLElement;

    // Every one of them, in the stack and nowhere else, and nothing in the stack but them.
    expect(bars().length).toBeGreaterThan(8);
    expect([...stack.children].map((fold) => fold.querySelector(":scope > button"))).toEqual(bars());
    for (const one of bars()) expect(one).toHaveClass("bar", "target");
  });

  test("test_with_a_group_open_the_settings_have_no_accessibility_fault", async () => {
    const { container } = render(<Settings spec={first} />);
    await user().click(bar(GREEN));

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("what the bar of a group says", () => {
  /** What the bar of a group says of what the group holds. `null` where it says nothing. */
  const heldBy = (name: string) => bar(name).querySelector(".holds")?.textContent ?? null;

  test("test_a_bar_says_what_its_group_holds_so_that_it_is_read_without_opening_anything", async () => {
    render(<Settings spec={first} />);
    // Closed, every one of them: what is set is still read.
    expect(standOpen()).toEqual([]);

    expect(heldBy(SETTINGS.money)).toBe("Renting, ideally up to £1,700 a month");
    expect(heldBy(SETTINGS.journeys)).toBe("Cindermoor Works, ideally within 35 minutes");
    expect(heldBy(STREETS)).toBe("Quiet streets");
    // What was asked for comes first, and then what Burro counts in every search.
    expect(heldBy(GREEN)).toBe(`Leafy. ${USUAL.onTheBar("Nearer a park")}`);
    expect(heldBy(GOING_OUT)).toBe(USUAL.onTheBar("Nearer a town centre"));
    expect(heldBy(SETTINGS.airAndNoise)).toBe(USUAL.onTheBar("Cleaner air, Less transport noise"));
    for (const name of [DIMENSION.brands, DIMENSION.crime, WHO_LIVES_THERE]) {
      expect([name, heldBy(name)]).toEqual([name, null]);
    }
  });

  test("test_what_a_bar_holds_is_heard_after_its_name_and_the_bar_is_found_by_its_name_alone", () => {
    render(<Settings spec={first} />);

    expect(bar(SETTINGS.money)).toHaveAccessibleName(SETTINGS.money);
    expect(bar(SETTINGS.money)).toHaveAccessibleDescription("Renting, ideally up to £1,700 a month");
    expect(bar(GREEN)).toHaveAccessibleName(GREEN);
    expect(bar(GREEN)).toHaveAccessibleDescription(`Leafy. ${USUAL.onTheBar("Nearer a park")}`);
    expect(bar(DIMENSION.brands)).toHaveAccessibleName(DIMENSION.brands);
    expect(bar(DIMENSION.brands)).toHaveAccessibleDescription("");
  });

  test("test_a_bar_says_the_same_open_as_closed_so_that_it_is_of_one_size_under_the_press_that_opens_it", async () => {
    render(<Settings spec={first} />);
    const before = bar(GREEN).textContent;
    const was = bar(GREEN).getAttribute("aria-expanded");

    await user().click(bar(GREEN));

    expect(bar(GREEN).getAttribute("aria-expanded")).not.toBe(was);
    expect(bar(GREEN).textContent).toBe(before);
    expect(heldBy(GREEN)).toBe(`Leafy. ${USUAL.onTheBar("Nearer a park")}`);
  });

  test("test_what_a_bar_says_is_the_search_as_the_api_last_returned_it", () => {
    const { rerender } = render(<Settings spec={first} />);
    expect(heldBy(SETTINGS.money)).toBe("Renting, ideally up to £1,700 a month");

    rerender(<Settings spec={{ ...first, budget: { ...first.budget, amount: 1850, strictness: "hard" } }} version={2} />);
    expect(heldBy(SETTINGS.money)).toBe("Renting, up to £1,850 a month");

    rerender(<Settings spec={{ ...first, tags: [] }} version={3} />);
    expect(heldBy(GREEN)).toBe(USUAL.onTheBar("Nearer a park"));
  });

  test("test_before_a_search_a_bar_says_only_what_burro_counts_in_every_search_for_nothing_else_is_set", () => {
    render(<Settings spec={meta.defaults.rent} />);
    const said = bars().map((one) => one.querySelector(".holds")?.textContent ?? null);

    expect(said.filter((holds) => holds !== null)).toEqual([
      USUAL.onTheBar("Nearer a town centre"),
      USUAL.onTheBar("Nearer a park"),
      expect.stringMatching(/^Counted in every search: .*Nearer a station/),
      USUAL.onTheBar("Cleaner air, Less transport noise"),
    ]);
    // Of the money and the journeys, where nothing is set, the name of each is all that it says.
    for (const name of [SETTINGS.money, SETTINGS.journeys]) expect(bar(name).textContent).toBe(name);
    expect(bars().map((one) => one.textContent)).toEqual(bars().map((one, at) => `${named(one)}${said[at] ?? ""}`));
  });

  test("test_the_drawing_of_a_group_is_dress_and_says_nothing", () => {
    render(<Settings spec={first} />);

    for (const one of bars()) {
      const drawn = one.querySelector(".drawn");
      expect(drawn).not.toBeNull();
      expect(within(drawn as HTMLElement).queryByRole("img")).toBeNull();
      expect(drawn?.firstElementChild).toHaveAttribute("aria-hidden", "true");
    }
  });
});

describe("every edge of the settings", () => {
  const COMPONENTS = path.resolve(__dirname, "..");
  const OWNED = ["SettingsPanel", "WeightSlider", "NumberStepper", "Disclosure"];

  test("test_no_edge_is_dashed_in_any_file_of_the_settings_the_slider_the_stepper_or_the_fold", () => {
    // The founder: "The dashed border is not understood to a user, please make solid".
    const files = OWNED.flatMap((folder) =>
      readdirSync(path.join(COMPONENTS, folder))
        .filter((name) => !/\.test\.tsx?$/.test(name))
        .map((name) => path.join(folder, name)),
    );
    const dashed = files.filter((file) => {
      const text = readFileSync(path.join(COMPONENTS, file), "utf8");
      return /\b(dashed|dotted)\b/.test(file.endsWith(".css") ? text.replace(/\/\*[\s\S]*?\*\//g, "") : text);
    });

    expect(files.length).toBeGreaterThan(15);
    expect(files.filter((file) => file.endsWith(".css")).length).toBeGreaterThanOrEqual(4);
    expect(dashed).toEqual([]);
  });
});
