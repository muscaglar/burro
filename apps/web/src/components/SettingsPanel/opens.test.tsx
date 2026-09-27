import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useEffect } from "react";

import { DIMENSION } from "@/content/labels";
import { FEATURES, SETTINGS } from "@/content/settings";
import { failed } from "@/lib/api/failure";
import { recordedAnswer } from "@/lib/api/recorded";
import type { PreferenceSpec } from "@/lib/api/schema";
import { NO_EDITS } from "@/lib/search/edits";
import { SearchProvider } from "@/lib/search/store";
import { SessionProvider, useSessionIfAny, type Session } from "@/lib/session/session";

import { faultsIn } from "../../../test/support/axe";
import { OPENS_AT_FIRST } from "./look";
import { SettingsPanel } from "./SettingsPanel";

const meta = recordedAnswer("get_meta", "meta").body.data;
/**
 * What the service calls each family of vibes, by the id of the family. A name is the
 * service's to write, and it has written two again: so a test finds a group by the name
 * the service gives it, and writes none down.
 */
const familyCalled = (id: string) => meta.families.find((one) => one.family === id)?.label ?? id;
const [STREETS, GOING_OUT, GREEN] = [familyCalled("streets_homes"), familyCalled("pace_food"), familyCalled("green")];
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
/** "Renting a 1 bed for about £1,700 a month, leafy and quiet, 35 minutes to Cindermoor Works", as it was ranked. */
const ranked = recordedAnswer("rank", "rank-first").body;
const first = ranked.data.spec;
const NAMED = { "syn-p0021": "Cindermoor Works" } as const;

/** What a search starts from, as a search that is open holds it: nothing in it was asked for. */
const nothingAsked: PreferenceSpec = { ...meta.defaults.rent };
/** Leafy and quiet, and nothing else: two vibes, of two families. */
const twoVibes: PreferenceSpec = { ...meta.defaults.rent, tags: first.tags };
/** The same, and a place to reach. */
const andAJourney: PreferenceSpec = { ...twoVibes, commutes: first.commutes };

interface Shown {
  readonly spec: PreferenceSpec;
  readonly version?: number;
  readonly standing?: boolean;
  /** Whether the page says the settings are open, where they are behind their button. */
  readonly opened?: boolean;
}

function Settings({ spec, version = 1, standing = true, opened = true }: Shown) {
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
      open={opened}
      onToggle={() => undefined}
      standing={standing}
    />
  );
}

/** Moves a slider of the settings, as a person does: what it sends is the settings' own. */
function move(name: string, to: number) {
  const slider = screen.getByRole("slider", { name });
  fireEvent.pointerDown(slider);
  fireEvent.change(slider, { target: { value: String(to) } });
  fireEvent.pointerUp(slider);
}

/** Everything a person can press, type in or move. */
const CONTROLS = "button, input, select, textarea, a[href]";
const bars = () => [...document.querySelectorAll<HTMLElement>("button[data-arrow][data-rest]")];
const named = (bar: HTMLElement) => bar.querySelector(".name")?.textContent ?? "";
/** The groups that stand open, by what each is called. */
const standOpen = () => bars().filter((bar) => bar.getAttribute("aria-expanded") === "true").map(named);
const bar = (name: string) => screen.getByRole("button", { name });
const user = () => userEvent.setup({ delay: null });

describe("the groups that stand open at first", () => {
  test("test_once_a_search_is_open_every_group_is_closed_which_one_line_chooses", () => {
    expect(OPENS_AT_FIRST).toBe("none");
  });

  test("test_before_a_search_the_first_two_groups_stand_open_so_that_it_is_seen_that_a_group_opens_and_closes", () => {
    // The founder: "Leave a couple of the accordians open by default to indicate this."
    render(<Settings spec={meta.defaults.rent} />);

    expect(standOpen()).toEqual([SETTINGS.money, SETTINGS.journeys]);
    expect(bars().length).toBeGreaterThan(8);
    // What an open group holds is on the page, under its bar, and what a closed one holds is not.
    expect(screen.getByRole("radio", { name: "Renting" })).toBeVisible();
    expect(screen.queryByRole("slider", { name: "Leafy" })).toBeNull();
  });

  test("test_once_a_search_is_open_every_group_is_closed_and_each_bar_says_what_it_holds", () => {
    // Walked at 1440 by 900: with "Refine search" open the settings were 2,022 px high,
    // because two groups stood open in it, and the first result went from 927 to 2,949. A
    // person has the answer before them, and opened the settings to change one thing.
    const { container } = render(<Settings spec={first} />);

    expect(standOpen()).toEqual([]);
    expect(bars().length).toBeGreaterThan(8);
    // All that is set is read on the bars, with nothing opened.
    expect(bar(SETTINGS.money).querySelector(".holds")?.textContent).toContain("Renting, ideally up to £1,700 a month");
    expect(bar(SETTINGS.journeys).querySelector(".holds")?.textContent).toContain("Cindermoor Works, ideally within 35 minutes");
    expect(bar(GREEN).querySelector(".holds")?.textContent).toContain("Leafy");
    expect(bar(STREETS).querySelector(".holds")?.textContent).toContain("Quiet streets");
    // Nothing a group holds is drawn: what can be pressed is the bars, one to a group.
    expect(screen.queryByRole("radio")).toBeNull();
    expect(screen.queryByRole("slider")).toBeNull();
    expect(container.querySelectorAll(CONTROLS)).toHaveLength(bars().length);
  });

  test.each([
    ["two vibes", twoVibes],
    ["a journey too", andAJourney],
    ["a scale", recordedAnswer("rank", "rank-scale").body.data.spec],
    ["a part of a vibe", recordedAnswer("rank", "rank-nights-out").body.data.spec],
    ["recorded crime", recordedAnswer("rank", "rank-crime-switched-on").body.data.spec],
    ["nothing that was asked for", nothingAsked],
  ])("test_whatever_the_search_holds_no_group_stands_open_at_first: %s", (_, spec) => {
    render(<Settings spec={spec} />);

    expect(standOpen()).toEqual([]);
  });

  test("test_the_groups_are_closed_behind_the_button_of_the_settings_as_where_they_stand_open", () => {
    render(<Settings spec={twoVibes} standing={false} />);

    expect(standOpen()).toEqual([]);
  });

  test("test_what_a_vibe_is_made_of_stands_open_where_a_part_of_it_was_asked_for_once_its_group_is_opened", async () => {
    // "Pubs and bars" was asked for, and is a part of going out.
    const nights = recordedAnswer("rank", "rank-nights-out").body.data.spec;
    render(<Settings spec={nights} />);

    await user().click(bar(GOING_OUT));

    expect(bar(FEATURES.madeOfName("Going out"))).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("switch", { name: "Pubs and bars" })).toBeChecked();
    // And is closed where none was.
    await user().click(bar(GREEN));
    expect(bar(FEATURES.madeOfName("Leafy"))).toHaveAttribute("aria-expanded", "false");
  });

  test("test_with_every_group_closed_and_with_one_opened_the_settings_have_no_accessibility_fault", async () => {
    const { container } = render(<Settings spec={first} />);
    expect(await faultsIn(container)).toEqual([]);

    await user().click(bar(GREEN));
    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("a group a person opened or closed", () => {
  test("test_a_press_on_a_bar_opens_its_group_and_a_second_closes_it_and_no_other_group_is_moved", async () => {
    render(<Settings spec={first} />);
    const press = user();

    await press.click(bar(GREEN));
    expect(standOpen()).toEqual([GREEN]);
    expect(bar(GREEN)).toHaveFocus();
    expect(screen.getByRole("slider", { name: "Leafy" })).toHaveValue("50");

    await press.click(bar(SETTINGS.money));
    expect(standOpen()).toEqual([SETTINGS.money, GREEN]);
    await press.click(bar(GREEN));
    expect(standOpen()).toEqual([SETTINGS.money]);
  });

  test("test_a_bar_is_opened_and_closed_by_the_keys_as_a_button_is", async () => {
    render(<Settings spec={first} />);
    const press = user();
    bar(GREEN).focus();

    await press.keyboard("{Enter}");
    expect(bar(GREEN)).toHaveAttribute("aria-expanded", "true");
    await press.keyboard(" ");
    expect(bar(GREEN)).toHaveAttribute("aria-expanded", "false");
    // Escape closes the group from what it holds, and the focus goes back to its bar.
    await press.keyboard("{Enter}");
    screen.getByRole("slider", { name: "Leafy" }).focus();
    await press.keyboard("{Escape}");
    expect(bar(GREEN)).toHaveAttribute("aria-expanded", "false");
    expect(bar(GREEN)).toHaveFocus();
  });

  test("test_a_group_a_person_opened_stays_open_as_the_search_changes_and_no_other_opens_of_itself", async () => {
    const { rerender } = render(<Settings spec={twoVibes} />);
    const press = user();
    await press.click(bar(GREEN));
    await press.click(bar(DIMENSION.brands));
    expect(standOpen()).toEqual([GREEN, DIMENSION.brands]);

    // More is typed, and read: the search holds a place to reach too, and then a budget.
    rerender(<Settings spec={andAJourney} version={2} />);
    expect(standOpen()).toEqual([GREEN, DIMENSION.brands]);
    rerender(<Settings spec={first} version={3} />);
    expect(standOpen()).toEqual([GREEN, DIMENSION.brands]);
    // What came to be asked for is read on the bar of its group, which is closed.
    expect(bar(SETTINGS.journeys).querySelector(".holds")?.textContent).toContain("Cindermoor Works");
  });

  test("test_what_the_settings_themselves_changed_opens_and_closes_no_group_under_a_persons_hand", async () => {
    // Seen in the rule as it was first written: worked out again at every answer, a group
    // closed as the last thing in it was taken off, under the hand that took it off.
    const calm = recordedAnswer("rank", "rank-scale").body.data.spec;
    const { rerender } = render(<Settings spec={calm} />);
    await user().click(bar(GOING_OUT));
    expect(standOpen()).toEqual([GOING_OUT]);

    // The person brings the scale back to its middle, which takes the vibe out of the search.
    move("Going out", 0);
    rerender(<Settings spec={nothingAsked} version={2} />);

    expect(standOpen()).toEqual([GOING_OUT]);
    expect(screen.getByRole("slider", { name: "Going out" })).toHaveValue("0");
  });

  test("test_a_search_that_the_settings_open_closes_no_group_under_the_hand_that_opened_it", async () => {
    // Before a search the first two groups stand open, and a person opens a third and
    // moves a slider in it. Where that opens the search, every group is as it was: the
    // two that stood open at first are not closed under the hand that is in the settings.
    const { rerender } = render(<Settings spec={meta.defaults.rent} />);
    await user().click(bar(GREEN));
    move("Leafy", 70);

    rerender(<Settings spec={{ ...meta.defaults.rent, tags: [{ tag_id: "leafy", weight: 0.7, toward: "high", provenance: "ui_edit" }] }} version={2} />);

    expect(standOpen()).toEqual([SETTINGS.money, SETTINGS.journeys, GREEN]);
  });

  test("test_a_search_that_opens_elsewhere_closes_the_two_groups_that_stood_open_to_show_that_they_fold", () => {
    // Seen in a browser, at 390 by 844: the settings are on the page from the first, behind
    // their button. They stood as a search starts when a sentence was read.
    const { rerender } = render(<Settings spec={meta.defaults.rent} standing={false} opened={false} />);
    expect(bars()).toEqual([]);

    rerender(<Settings spec={twoVibes} version={2} standing={false} opened={false} />);
    rerender(<Settings spec={twoVibes} version={2} standing={false} opened />);

    expect(standOpen()).toEqual([]);
  });

  test("test_where_the_settings_stand_open_they_follow_a_search_that_changes_elsewhere", () => {
    const { rerender } = render(<Settings spec={meta.defaults.rent} />);
    expect(standOpen()).toEqual([SETTINGS.money, SETTINGS.journeys]);

    // A sentence is read, and then a chip is taken off: the hand is in neither case in the settings.
    rerender(<Settings spec={recordedAnswer("rank", "rank-scale").body.data.spec} version={2} />);
    expect(standOpen()).toEqual([]);
    rerender(<Settings spec={twoVibes} version={3} />);
    expect(standOpen()).toEqual([]);
    // And a person starts again: the settings are as they first stood.
    rerender(<Settings spec={meta.defaults.rent} version={4} />);
    expect(standOpen()).toEqual([SETTINGS.money, SETTINGS.journeys]);
  });

  test("test_starting_again_after_an_edit_that_was_never_answered_sets_the_settings_as_they_first_stood", async () => {
    // Burro could not be reached, and the edit of the settings has no answer. To start
    // again is no answer to it either, whatever the count of answers says.
    const { rerender } = render(<Settings spec={twoVibes} />);
    await user().click(bar(GREEN));
    move("Leafy", 70);

    rerender(<Settings spec={meta.defaults.rent} version={2} />);

    expect(standOpen()).toEqual([SETTINGS.money, SETTINGS.journeys]);
  });

  test("test_an_answer_that_changes_nothing_of_the_search_moves_no_group", async () => {
    // Reasons come in, an edit is refused: the search is the one it was.
    const { rerender } = render(<Settings spec={first} />);
    await user().click(bar(SETTINGS.journeys));

    rerender(<Settings spec={first} version={2} />);
    rerender(<Settings spec={first} version={3} />);

    expect(standOpen()).toEqual([SETTINGS.journeys]);
  });

  test("test_when_a_person_starts_again_the_settings_are_as_they_first_stood", async () => {
    const { rerender } = render(<Settings spec={twoVibes} />);
    const press = user();
    await press.click(bar(GREEN));
    await press.click(bar(DIMENSION.crime));
    expect(standOpen()).toEqual([GREEN, DIMENSION.crime]);

    // The search is what a search starts from again.
    rerender(<Settings spec={meta.defaults.rent} version={2} />);

    expect(standOpen()).toEqual([SETTINGS.money, SETTINGS.journeys]);
  });
});

describe("what was opened and closed, kept while the page is open", () => {
  /** The session of the page that was last drawn. */
  let caught: Session | null = null;
  const keep = (session: Session | null) => {
    caught = session;
  };
  /** Tells the test which session the page stands in, once the page is drawn. */
  function Caught({ tell }: { tell: (session: Session | null) => void }) {
    const session = useSessionIfAny();
    useEffect(() => tell(session), [tell, session]);
    return null;
  }
  /** A page with a session and a search, as the shell and the search page make them. */
  function Page({ spec, shown = true }: { spec: PreferenceSpec; shown?: boolean }) {
    return (
      <SessionProvider>
        <SearchProvider meta={meta} areas={areas}>
          <Caught tell={keep} />
          {shown ? <Settings spec={spec} /> : null}
        </SearchProvider>
      </SessionProvider>
    );
  }
  const search = () => caught?.search()?.store;
  /** The search is ranked, as when a sentence was read: it is open from then on. */
  const begin = () => act(() => search()?.dispatch({ type: "rank_answered", data: ranked.data, sent: NO_EDITS, meta: ranked.meta }));
  const startAgain = () => act(() => search()?.dispatch({ type: "started_again" }));

  test("test_what_a_person_opened_is_open_again_when_the_settings_are_taken_off_the_page_and_put_back", async () => {
    // The settings stand in a fold after a search, and are taken off the page while it is closed.
    const { rerender } = render(<Page spec={twoVibes} />);
    begin();
    const press = user();
    await press.click(bar(STREETS));
    await press.click(bar(DIMENSION.brands));
    await press.click(bar(FEATURES.madeOfName("Quiet streets")));
    const asTheyLeftIt = [STREETS, DIMENSION.brands];
    expect(standOpen()).toEqual(asTheyLeftIt);

    rerender(<Page spec={twoVibes} shown={false} />);
    expect(bars()).toEqual([]);
    rerender(<Page spec={twoVibes} />);

    expect(standOpen()).toEqual(asTheyLeftIt);
    expect(bar(FEATURES.madeOfName("Quiet streets"))).toHaveAttribute("aria-expanded", "true");
  });

  test("test_put_back_the_settings_open_nothing_of_what_came_to_be_asked_for_while_they_were_off_the_page", async () => {
    const { rerender } = render(<Page spec={twoVibes} />);
    begin();
    await user().click(bar(GREEN));
    expect(standOpen()).toEqual([GREEN]);

    rerender(<Page spec={twoVibes} shown={false} />);
    // More was typed and read meanwhile: a place to reach is asked for now.
    rerender(<Page spec={andAJourney} />);

    // What the person opened is open, and what nobody touched is closed: its bar says what it holds.
    expect(standOpen()).toEqual([GREEN]);
    expect(bar(SETTINGS.journeys).querySelector(".holds")?.textContent).toContain("Cindermoor Works");
  });

  test("test_what_was_opened_is_forgotten_when_a_person_starts_again_while_the_settings_are_off_the_page", async () => {
    const { rerender } = render(<Page spec={first} />);
    begin();
    await user().click(bar(DIMENSION.brands));
    expect(standOpen()).toEqual([DIMENSION.brands]);

    rerender(<Page spec={first} shown={false} />);
    startAgain();
    rerender(<Page spec={meta.defaults.rent} />);

    expect(standOpen()).toEqual([SETTINGS.money, SETTINGS.journeys]);
  });

  test("test_what_was_opened_before_a_search_is_forgotten_by_a_search_that_was_begun_and_begun_again_unseen", async () => {
    // The settings stand in one place before a search and in another after it: a person may
    // open a group, search in words, and start again without seeing the settings between.
    const { rerender } = render(<Page spec={meta.defaults.rent} />);
    await user().click(bar(GREEN));
    expect(standOpen()).toEqual([SETTINGS.money, SETTINGS.journeys, GREEN]);

    rerender(<Page spec={meta.defaults.rent} shown={false} />);
    begin();
    startAgain();
    rerender(<Page spec={meta.defaults.rent} />);

    expect(standOpen()).toEqual([SETTINGS.money, SETTINGS.journeys]);
  });

  test("test_what_was_opened_before_a_search_stays_open_into_the_search_and_what_stood_open_to_show_does_not", async () => {
    const { rerender } = render(<Page spec={meta.defaults.rent} />);
    await user().click(bar(GREEN));

    rerender(<Page spec={meta.defaults.rent} shown={false} />);
    begin();
    rerender(<Page spec={first} />);

    // Green is open by the press. The first two stood open to show that a group folds, and nobody opened them.
    expect(standOpen()).toEqual([GREEN]);
  });

  test("test_one_page_keeps_nothing_of_what_was_opened_on_another", async () => {
    const one = render(<Page spec={first} />);
    await user().click(bar(DIMENSION.brands));
    expect(standOpen()).toContain(DIMENSION.brands);
    one.unmount();

    render(<Page spec={first} />);

    expect(standOpen()).not.toContain(DIMENSION.brands);
  });

  test("test_what_is_kept_is_kept_in_memory_and_nowhere_a_browser_keeps_things", async () => {
    const stored = jest.spyOn(Storage.prototype, "setItem");
    try {
      render(<Page spec={first} />);
      await user().click(bar(DIMENSION.brands));

      expect(stored).not.toHaveBeenCalled();
      expect(document.cookie).toBe("");
      expect(window.location.href).not.toMatch(/brands|made|family/);
    } finally {
      stored.mockRestore();
    }
  });
});
