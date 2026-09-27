import { render, screen, within } from "@testing-library/react";

import { SETTINGS } from "@/content/settings";
import { USUAL } from "@/content/usual";
import { failed } from "@/lib/api/failure";
import { recordedAnswer } from "@/lib/api/recorded";
import type { PreferenceSpec } from "@/lib/api/schema";

import { faultsIn } from "../../../test/support/axe";
import { groupsOf } from "./groups";
import { NAMED_IN_SIGHT_ARE, SAYS_AT_THEIR_HEAD_ARE } from "./look";
import { SettingsPanel } from "./SettingsPanel";

// The other way of each of the two lines that choose what stands at the head of the
// settings. The founder asked for their sentences to go and named them, and the website is
// left so. What is not the tab's to say, and what they were before they had a name of the
// founder's, is one line away each: it is held here, as what is chosen is held in the test
// beside this one, so that either may be chosen.
jest.mock("./look", () => ({
  ...jest.requireActual<typeof import("./look")>("./look"),
  SAYS_AT_THEIR_HEAD: "what-counts",
  NAMED_IN_SIGHT: "before-a-search",
}));

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
/** "Renting a 1 bed for about £1,700 a month, leafy and quiet, 35 minutes to Cindermoor Works", as it was ranked. */
const first = recordedAnswer("rank", "rank-first").body.data.spec;
const NAMED = { "syn-p0021": "Cindermoor Works" } as const;

/** What a search starts from, as a search that is open holds it: nothing in it was asked for. */
const nothingAsked: PreferenceSpec = { ...meta.defaults.rent };
/** What Burro counts in every search, of renting, by the names the API gives, in the order of the groups. */
const SIX = groupsOf(meta.defaults.rent, meta, areas, NAMED).flatMap((group) => group.usual);

function Settings({ spec }: { readonly spec: PreferenceSpec }) {
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
      version={1}
      open
      onToggle={() => undefined}
      standing
    />
  );
}

const settings = () => screen.getByRole("region", { name: SETTINGS.title });
/** Every sentence at the head of the settings, over their groups, in the order they stand. */
const head = () => [...settings().querySelectorAll(":scope > p")].map((line) => line.textContent);

describe("the head of the settings, where it names what burro counts in every search", () => {
  test("test_each_of_the_two_lines_chooses_between_two_ways", () => {
    expect(SAYS_AT_THEIR_HEAD_ARE).toEqual(["nothing", "what-counts"]);
    expect(NAMED_IN_SIGHT_ARE).toEqual(["always", "before-a-search"]);
  });

  test("test_it_says_one_thing_which_the_tab_does_not_and_never_what_the_tab_says", () => {
    // What the founder had taken out is what was said twice. It is out by either way.
    for (const spec of [meta.defaults.rent, first, nothingAsked]) {
      const { unmount } = render(<Settings spec={spec} />);
      const said = settings().textContent ?? "";
      expect(head()).toHaveLength(1);
      expect(/in the groups below|straight away|do the same job as typing/.test(said)).toBe(false);
      unmount();
    }
  });

  test("test_before_a_search_it_names_them_and_says_nothing_of_a_ranking", () => {
    render(<Settings spec={meta.defaults.rent} />);

    expect(head()).toEqual([USUAL.before(SIX)]);
  });

  test("test_once_a_search_is_open_it_names_them_and_says_that_each_counts_for_much_less_than_what_was_asked_for", () => {
    render(<Settings spec={first} />);

    expect(head()).toEqual([USUAL.little(SIX)]);
    for (const name of SIX) expect(head()[0]).toContain(name);
    // It is so: what nobody chose counts for a tenth at the most, and what was asked for three times that.
    const usual = first.weights.filter((weight) => weight.provenance === "default").map((weight) => weight.weight);
    expect(Math.max(...usual)).toBeLessThanOrEqual(0.1);
    expect(Math.min(...first.tags.map((tag) => tag.weight), first.budget.weight, first.commute_weight)).toBeGreaterThanOrEqual(0.3);
  });

  test("test_how_much_they_count_is_said_only_where_it_is_so", () => {
    // Leafy is asked for, and counts for as little as what nobody chose.
    const faint = { ...first, tags: first.tags.map((tag) => ({ ...tag, weight: 0.1 })) };
    const { unmount } = render(<Settings spec={faint} />);
    expect(head()).toEqual([USUAL.also(SIX)]);
    unmount();

    // Nothing was asked for, as when the settings are ranked as they stand.
    render(<Settings spec={nothingAsked} />);
    expect(head()).toEqual([USUAL.alone(SIX)]);
  });

  test("test_a_setting_a_person_changed_is_theirs_and_is_named_with_the_rest_no_longer", () => {
    const park = first.weights.find((weight) => weight.feature_id === "park_proximity");
    const changed = {
      ...first,
      weights: first.weights.map((weight) => (weight === park ? { ...weight, weight: 0.6, provenance: "ui_edit" as const } : weight)),
    };
    render(<Settings spec={changed} />);

    expect(head()).toEqual([USUAL.little(SIX.filter((name) => name !== "Nearer a park"))]);
  });

  test("test_where_nothing_is_counted_that_nobody_chose_nothing_is_said_of_it", () => {
    const none = { ...first, weights: first.weights.map((weight) => ({ ...weight, weight: 0, provenance: "ui_edit" as const })) };
    render(<Settings spec={none} />);

    expect(head()).toEqual([]);
    expect(/in every search/.test(settings().textContent ?? "")).toBe(false);
  });
});

describe("the name of the settings, where it is drawn before a search alone", () => {
  test("test_before_a_search_their_name_stands_over_them", () => {
    render(<Settings spec={meta.defaults.rent} />);

    expect(within(settings()).getByRole("heading", { level: 2, name: SETTINGS.title })).toBeVisible();
  });

  test("test_once_a_search_is_open_no_heading_stands_under_the_button_that_opened_them_and_they_are_still_found_by_name", () => {
    // Walked, of the name they had: "Refine search" opened onto a box headed "Settings".
    render(<Settings spec={first} />);

    expect(screen.queryByRole("heading", { name: SETTINGS.title })).toBeNull();
    expect(within(settings()).queryAllByRole("heading")).toEqual([]);
    expect(settings().tagName).toBe("SECTION");
    expect(settings()).toHaveAccessibleName(SETTINGS.title);
  });

  test("test_with_every_state_of_their_head_the_settings_have_no_accessibility_fault", async () => {
    for (const spec of [meta.defaults.rent, first, nothingAsked]) {
      const { container, unmount } = render(<Settings spec={spec} />);
      expect(await faultsIn(container)).toEqual([]);
      unmount();
    }
  });
});
