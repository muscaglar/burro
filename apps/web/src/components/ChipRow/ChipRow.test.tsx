import { readFileSync } from "node:fs";
import path from "node:path";

import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { COMBINE } from "@/content/labels";
import { CHIPS, PLACE, REJECTED, TENURE_CHOICE } from "@/content/search";
import { BUDGET, JOURNEY, SLIDER } from "@/content/settings";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Operations, PreferenceSpec, RejectReason, Tenure } from "@/lib/api/schema";
import { edits } from "@/lib/search/edits";
import type { Assumed } from "@/lib/search/state";

import { faultsIn } from "../../../test/support/axe";
import { isFor, rulesOf, subjectOf } from "../../../test/support/css";
import { ChipRow, SHOWN_AT_FIRST } from "./ChipRow";

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const first = recordedAnswer("interpret", "interpret-first").body.data;
const two = recordedAnswer("interpret", "interpret-two-journeys").body.data;
const ASSUMED: Assumed = { budget: ["strictness"], "place:syn-p0021": ["mode", "strictness"] };

/** True when the words are drawn where a person who sees the page can read them. */
const canBeSeen = (element: HTMLElement) =>
  element.closest(".visually-hidden, [aria-hidden='true'], [hidden]") === null;

interface Shown {
  tenurePicked?: boolean;
  quoted?: Record<string, string>;
  assumed?: Assumed;
  refused?: ReadonlyMap<string, RejectReason>;
  waiting?: boolean;
  readBy?: "rule" | "model" | null;
  placeNames?: Record<string, string>;
  form?: typeof meta;
  /** True to leave the row as it first stands: the first few chips, in short. */
  inARow?: boolean;
}

function show(
  spec: PreferenceSpec = first.spec,
  {
    assumed = ASSUMED,
    refused,
    waiting = false,
    readBy = "rule" as const,
    placeNames = { "syn-p0021": "Cindermoor Works" },
    tenurePicked = false,
    quoted = {},
    form = meta,
    inARow = false,
  }: Shown = {},
) {
  const sent: Operations[] = [];
  const tenures: Tenure[] = [];
  const onOpenSettings = jest.fn();
  const view = render(
    <ChipRow
      spec={spec}
      assumed={assumed}
      placeNames={placeNames}
      meta={form}
      areas={areas}
      onEdit={(operations) => sent.push(operations)}
      onTenure={(tenure) => tenures.push(tenure)}
      onOpenSettings={onOpenSettings}
      version={1}
      refused={refused}
      readBy={readBy}
      waiting={waiting}
      tenurePicked={tenurePicked}
      quoted={quoted}
    />,
  );
  // Most of what is held here is of the chips in full, which are one press away.
  const rest = screen.queryByRole("button", { name: /^\+\d+ more$/ });
  if (!inARow && rest !== null) fireEvent.click(rest);
  return { sent, tenures, onOpenSettings, user: userEvent.setup({ delay: null }), ...view };
}

const chips = () => screen.getAllByRole("listitem");
const heading = () => screen.getByRole("heading", { level: 2 });
/** What a chip says of itself: its words, and not what it opens to nor its way out. */
const wordsOf = (chip: HTMLElement) => (chip.querySelector("[data-main]") ?? chip.querySelector("span"))?.textContent ?? "";
/** A search of more things than stand in the row at first: five vibes, a place, a budget and the tenure. */
const many: PreferenceSpec = {
  ...first.spec,
  tags: [
    ...first.spec.tags,
    ...(["village_feel", "parks_close_by", "foodie"] as const).map((tag_id) => ({
      tag_id,
      weight: 0.5,
      toward: "high" as const,
      provenance: "stated" as const,
    })),
  ],
};

describe("the chips", () => {
  test("test_each_part_nobody_chose_carries_the_word_assumed", async () => {
    const { user } = show();

    // A chip that is opened opens the row out, and every chip then says every part of itself.
    await user.click(screen.getByRole("button", { name: /^Cindermoor Works/ }));

    expect(chips().map(wordsOf)).toEqual([
      "Leafy",
      "Quiet streets",
      "Cindermoor Works, Public transport assumed, within 35 minutes, flexible assumed",
      "£1,700 a month, One bedroom, flexible assumed",
      "Renting",
      "Usual settings: 6 assumed",
    ]);
    // The word says it. The dashed edge repeats it for the eye.
    expect(chips().map((chip) => chip.getAttribute("data-assumed"))).toEqual([
      "false",
      "false",
      "true",
      "true",
      "false",
      "true",
    ]);
  });

  test("test_a_tenure_nobody_said_carries_the_word_assumed_unless_the_person_picked_it", () => {
    show(meta.defaults.buy, { assumed: {}, readBy: null });
    expect(chips()[0]?.textContent).toBe(`Buying ${CHIPS.assumed}`);

    cleanup();
    show(meta.defaults.buy, { assumed: {}, readBy: null, tenurePicked: true });
    expect(chips()[0]?.textContent).toBe("Buying");
    expect(chips()[0]).toHaveAttribute("data-assumed", "false");
  });

  test("test_removing_a_chip_moves_the_focus_to_the_chip_beside_it_and_never_leaves_it_on_nothing", async () => {
    // Seen in a browser: after a chip was removed with the keyboard the focus was on nothing.
    // The button that was pressed goes with its chip when the answer comes.
    const { user, sent } = show();
    const remove = screen.getByRole("button", { name: `${CHIPS.remove}: Leafy` });
    remove.focus();

    await user.keyboard("{Enter}");

    expect(sent).toEqual([edits.tagOff("leafy")]);
    // The chip after it, which is still there when Leafy has gone.
    expect(screen.getByRole("button", { name: /^Quiet streets/ })).toHaveFocus();
  });

  test("test_removing_the_last_chip_that_can_be_removed_moves_the_focus_to_a_chip_that_stays", async () => {
    const { user } = show({ ...first.spec, weights: first.spec.weights.filter((weight) => weight.provenance !== "default") });
    const last = screen.getByRole("button", { name: `${CHIPS.remove}: £1,700 a month` });
    last.focus();

    await user.keyboard("{Enter}");

    expect(document.activeElement).not.toBe(document.body);
    expect(document.activeElement).not.toBe(last);
    // The tenure comes after it, and cannot be removed.
    expect(screen.getByRole("button", { name: /^Renting/ })).toHaveFocus();
  });

  test("test_the_chips_can_be_given_the_focus_by_the_page_and_are_no_stop_of_their_own", () => {
    show();

    // A question that is answered goes, and the focus goes to what the answer changes.
    expect(screen.getByRole("region", { name: CHIPS.label })).toHaveAttribute("tabindex", "-1");
  });

  test("test_a_chip_opens_the_control_the_settings_hold_in_place_and_one_is_open_at_a_time", async () => {
    const { user } = show();

    const chipOf = (name: RegExp) => screen.getByRole("button", { name }).closest("li") as HTMLElement;

    await user.click(screen.getByRole("button", { name: /^£1,700 a month/ }));
    expect(screen.getByRole("button", { name: /^£1,700 a month/ })).toHaveAttribute("aria-expanded", "true");
    expect(within(chipOf(/^£1,700 a month/)).getByRole("group", { name: BUDGET.legend })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /^Cindermoor Works/ }));
    expect(screen.queryByRole("group", { name: BUDGET.legend })).toBeNull();
    expect(
      within(chipOf(/^Cindermoor Works/)).getByRole("group", { name: JOURNEY.place("Cindermoor Works") }),
    ).toBeInTheDocument();
    // One chip is open at a time. The button that shows the rest says that the row is opened out.
    expect(screen.getAllByRole("button", { expanded: true }).filter((one) => "main" in one.dataset)).toHaveLength(1);
  });

  test("test_the_control_in_a_chip_sends_the_same_edit_as_the_one_in_the_settings", async () => {
    const { user, sent } = show();

    await user.click(screen.getByRole("button", { name: /^£1,700 a month/ }));
    await user.click(screen.getByRole("checkbox", { name: BUDGET.firm }));
    await user.click(screen.getByRole("button", { name: /^Leafy/ }));
    // The slider of a vibe, taken down to nothing, takes the vibe out of the search.
    fireEvent.change(screen.getByRole("textbox", { name: SLIDER.number("Leafy") }), { target: { value: "0" } });
    fireEvent.blur(screen.getByRole("textbox", { name: SLIDER.number("Leafy") }));

    expect(sent).toEqual([edits.budgetStrictness("hard"), edits.tagOff("leafy")]);
  });

  test("test_the_tenure_chip_opens_the_choice_of_renting_or_buying", async () => {
    const { user, tenures, sent } = show();

    await user.click(screen.getByRole("button", { name: /^Renting/ }));
    await user.click(screen.getByRole("radio", { name: TENURE_CHOICE.buy }));

    expect(tenures).toEqual(["buy"]);
    expect(sent).toEqual([]);
  });

  test("test_a_chip_has_a_remove_button_where_the_setting_can_be_removed", async () => {
    const { user, sent } = show();

    expect(screen.getAllByRole("button", { name: /^Remove: / }).map((button) => button.getAttribute("aria-label"))).toEqual([
      "Remove: Leafy",
      "Remove: Quiet streets",
      "Remove: Cindermoor Works",
      "Remove: £1,700 a month",
    ]);
    await user.click(screen.getByRole("button", { name: "Remove: Cindermoor Works" }));
    await user.click(screen.getByRole("button", { name: "Remove: £1,700 a month" }));

    expect(sent).toEqual([edits.placeRemove("syn-p0021"), edits.budgetClear()]);
  });

  test("test_escape_closes_an_open_chip_and_puts_the_focus_back_on_it", async () => {
    const { user } = show();
    const chip = screen.getByRole("button", { name: /^Cindermoor Works/ });

    await user.click(chip);
    await user.tab();
    await user.keyboard("{Escape}");

    expect(chip).toHaveAttribute("aria-expanded", "false");
    expect(chip).toHaveFocus();
  });

  test("test_the_usual_settings_chip_opens_the_settings", async () => {
    const { user, onOpenSettings } = show();

    await user.click(screen.getByRole("button", { name: /^Usual settings: 6/ }));
    expect(onOpenSettings).toHaveBeenCalledTimes(1);

    // Once the row is opened out, what the usual settings are is said, and describes the chip.
    await user.click(screen.getByRole("button", { name: /^Renting/ }));
    expect(screen.getByRole("button", { name: /^Usual settings: 6/ })).toHaveAccessibleDescription(
      `${CHIPS.usualHint} ${CHIPS.openSettings}`,
    );
  });

  test("test_what_the_usual_settings_are_is_said_where_it_can_be_seen", async () => {
    const { user } = show();
    await user.click(screen.getByRole("button", { name: /^Renting/ }));

    // It was written, and then hidden from everyone who can see the page.
    const hint = screen.getByText(`${CHIPS.usualHint} ${CHIPS.openSettings}`);
    expect(canBeSeen(hint)).toBe(true);
    // It is said once, and the chip is described by it and not by a second copy.
    expect(screen.getAllByText(CHIPS.usualHint, { exact: false })).toHaveLength(1);
  });

  test("test_with_no_usual_setting_left_nothing_is_said_of_them", () => {
    show({ ...first.spec, weights: first.spec.weights.filter((weight) => weight.provenance !== "default") });

    expect(screen.queryByText(CHIPS.usualHint, { exact: false })).toBeNull();
  });

  test("test_what_assumed_means_is_said_once_wherever_anything_is_marked_so", async () => {
    const { user } = show();
    await user.click(screen.getByRole("button", { name: /^Renting/ }));
    expect(canBeSeen(screen.getByText(CHIPS.assumedHint))).toBe(true);
    expect(CHIPS.assumedHint).toContain(CHIPS.assumed);

    cleanup();
    const stated = {
      ...first.spec,
      tenure_from: "stated" as const,
      commutes: [],
      weights: first.spec.weights.filter((weight) => weight.provenance !== "default"),
    };
    const again = show(stated, { assumed: {} });
    await again.user.click(screen.getByRole("button", { name: /^Renting/ }));
    expect(chips().map((chip) => chip.getAttribute("data-assumed"))).not.toContain("true");
    expect(screen.queryByText(CHIPS.assumedHint)).toBeNull();
  });

  test("test_where_a_journey_and_a_budget_outweigh_the_place_the_chips_say_how_to_change_it", async () => {
    // What was asked of the place leads, so as the search was read nothing is said.
    const asked = show();
    await asked.user.click(screen.getByRole("button", { name: /^Renting/ }));
    expect(screen.queryByText(CHIPS.leadsHint)).toBeNull();

    cleanup();
    // Once a person has made the journey and the budget count for more, the line over the chips
    // says that they count most. With the chips opened out, one line says why, and where a
    // person can change it.
    const led = { ...first.spec, commute_weight: 1, budget: { ...first.spec.budget, weight: 0.8 } };
    const { user } = show(led);
    expect(screen.queryByText(CHIPS.leadsHint)).toBeNull();
    await user.click(screen.getByRole("button", { name: /^Renting/ }));
    expect(canBeSeen(screen.getByText(CHIPS.leadsHint))).toBe(true);

    cleanup();
    // With nothing asked of the place, nothing is outweighed, and nothing is said.
    const money = recordedAnswer("interpret", "interpret-money-and-work").body.data.spec;
    const again = show(money, { assumed: {} });
    await again.user.click(screen.getByRole("button", { name: /^Renting/ }));
    expect(screen.queryByText(CHIPS.leadsHint)).toBeNull();
  });

  test("test_the_usual_settings_chip_is_named_in_a_few_words_and_its_hint_is_said_once", () => {
    show();

    // The hint describes the button. Were it inside the button it would be its name as well.
    expect(screen.getByRole("button", { name: /^Usual settings: 6/ })).toHaveAccessibleName(
      `Usual settings: 6 ${CHIPS.assumed}`,
    );
  });

  test("test_a_thing_that_was_taken_off_says_so_has_no_remove_button_and_opens_its_switch_off", async () => {
    const second = recordedAnswer("interpret", "interpret-second-sentence").body.data.spec;
    // A feature is named by the plain name the API gives it.
    const highStreet = "Nearer a town centre";
    const { user, sent } = show(second);

    const chip = screen.getByRole("button", { name: new RegExp(`^${highStreet}`) });
    expect(chip).toHaveTextContent(`${highStreet}, ${CHIPS.off}`);
    expect(screen.queryByRole("button", { name: `${CHIPS.remove}: ${highStreet}` })).toBeNull();
    expect(screen.getByRole("button", { name: `${CHIPS.remove}: More public parks and gardens` })).toBeInTheDocument();

    await user.click(chip);
    expect(screen.getByRole("switch", { name: highStreet })).not.toBeChecked();
    await user.click(screen.getByRole("switch", { name: highStreet }));

    expect(sent).toEqual([edits.featureOn("highstreet_access")]);
  });

  test("test_a_hidden_area_is_a_chip_that_can_be_removed_and_opens_nothing", async () => {
    const hidden = { ...first.spec, areas: [{ area_id: "syn-n0006", rule: "exclude", provenance: "ui_edit" }] } as const;
    const { user, sent } = show(hidden);

    expect(screen.queryByRole("button", { name: /^Farrowmere/ })).toBeNull();
    expect(screen.getByText("Farrowmere")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Remove: Farrowmere" }));

    expect(sent).toEqual([edits.areaClear("syn-n0006")]);
  });

  test("test_the_chips_have_a_heading_that_can_be_seen_and_says_what_they_are", () => {
    // Before anything is read, the chips are what a search starts from: nobody said them.
    show(meta.defaults.rent, { readBy: null, assumed: {} });
    expect(heading()).toHaveTextContent(CHIPS.startLabel);
    expect(canBeSeen(heading())).toBe(true);
    expect(screen.getByRole("region", { name: CHIPS.startLabel })).toBeInTheDocument();

    // Words that were read into nothing leave the search where it started.
    cleanup();
    show(meta.defaults.buy, { readBy: "rule", assumed: {} });
    expect(heading()).toHaveTextContent(CHIPS.startLabel);

    // Once words have been read into a search, the chips are what was understood.
    cleanup();
    show();
    expect(heading()).toHaveTextContent(CHIPS.label);
    expect(canBeSeen(heading())).toBe(true);

    // A search made with the settings alone was not understood from anything.
    cleanup();
    show(first.spec, { readBy: null });
    expect(heading()).toHaveTextContent(CHIPS.setLabel);

    // While the first sentence is read, what is held a place for is what will be understood.
    cleanup();
    show(meta.defaults.rent, { readBy: null, waiting: true });
    expect(heading()).toHaveTextContent(CHIPS.label);
  });

  test("test_a_place_is_shown_by_its_name_and_never_by_a_number", () => {
    // Seen in a browser: one of two workplaces was shown as "Place 1". Every answer now
    // names every place of its spec, and the chips are drawn from those names.
    show(two.spec, { assumed: {}, placeNames: Object.fromEntries(two.places.map((one) => [one.place_id, one.name])) });

    expect(two.spec.commutes.map((commute) => commute.place_id)).toEqual(["syn-p0019", "syn-p0026"]);
    expect(chips().map((chip) => chip.textContent?.replace("×", "").split(",")[0])).toEqual(
      expect.arrayContaining(["Foxholt Market", "Wexmoor University"]),
    );
    expect(chips().filter((chip) => /\bPlace \d/.test(chip.textContent ?? ""))).toEqual([]);
    expect(screen.queryByText(/cannot show the name/)).toBeNull();
  });

  test("test_a_place_an_answer_gave_no_name_for_is_said_to_have_none", () => {
    // It cannot happen while the API keeps its contract. If it does, the chip says so.
    show(first.spec, { placeNames: {} });

    expect(chips().map(wordsOf).filter((words) => words.startsWith(PLACE.noName))).toHaveLength(1);
    expect(PLACE.noName).not.toMatch(/\d/);
  });

  test("test_with_two_places_a_chip_says_which_journey_counts_and_that_nobody_chose_it", async () => {
    // With two places only one journey feeds the fit, unless the person says otherwise.
    // It was said nowhere but in the settings, which are closed at first.
    const { user, sent } = show(two.spec, {
      assumed: {},
      placeNames: { "syn-p0019": "Foxholt Market", "syn-p0026": "Wexmoor University" },
    });
    const names = chips().map((chip) => chip.textContent?.replace("×", ""));

    expect(two.spec).toMatchObject({ commute_combine: "slowest", commute_combine_from: "default" });
    expect(names).toContain(`${COMBINE.slowest} ${CHIPS.assumed}`);
    // It comes after the places it is about.
    expect(names.findIndex((name) => name?.startsWith(COMBINE.slowest))).toBe(
      names.findIndex((name) => name?.startsWith("Wexmoor University")) + 1,
    );

    await user.click(screen.getByRole("button", { name: new RegExp(`^${COMBINE.slowest}`) }));
    await user.click(screen.getByRole("radio", { name: COMBINE.mean }));

    expect(sent).toEqual([edits.journeyCombine("mean")]);
    expect(screen.queryByRole("button", { name: `${CHIPS.remove}: ${COMBINE.slowest}` })).toBeNull();
  });

  test("test_once_it_was_chosen_the_chip_for_which_journey_counts_is_not_marked_assumed", () => {
    show(
      { ...two.spec, commute_combine: "mean", commute_combine_from: "ui_edit" },
      { assumed: {}, placeNames: { "syn-p0019": "Foxholt Market", "syn-p0026": "Wexmoor University" } },
    );

    expect(chips().map((chip) => chip.textContent?.replace("×", ""))).toContain(COMBINE.mean);
  });

  test("test_with_one_place_no_chip_says_which_journey_counts", () => {
    show();

    expect(first.spec.commutes).toHaveLength(1);
    expect(screen.queryByText(COMBINE.slowest)).toBeNull();
    expect(screen.queryByText(COMBINE.mean)).toBeNull();
  });

  test("test_which_journey_counts_is_said_as_it_is_worked_out", () => {
    // It is the journey that does worst against its own limit, which need not be the one
    // that takes the most minutes. "The slowest" would be untrue of it.
    const contract = readFileSync(path.resolve(__dirname, "../../../../../docs/design/contract.md"), "utf8");

    expect(contract).toContain("`slowest`, the default, takes the `min` of the destinations' utilities");
    expect(COMBINE.slowest).toMatch(/worst against its limit/);
    expect(COMBINE.slowest).not.toMatch(/slowest/);
  });

  test("test_who_read_the_words_is_said_in_words_a_newcomer_knows", () => {
    // "Read by rules." says nothing to someone who does not know there are two readers.
    expect(CHIPS.readBy.rule).toMatch(/without AI/);
    expect(CHIPS.readBy.model).toMatch(/by AI/);
  });

  test("test_who_read_the_words_is_said_beside_the_heading_whether_or_not_the_row_is_opened_out", () => {
    show(many, { inARow: true });

    expect(canBeSeen(screen.getByText(CHIPS.readBy.rule))).toBe(true);
    expect(screen.getByRole("button", { name: CHIPS.rest(2) })).toHaveAttribute("aria-expanded", "false");
  });

  test("test_the_line_under_the_chips_says_who_read_the_words", () => {
    show();
    expect(screen.getByText(CHIPS.readBy.rule)).toBeInTheDocument();

    cleanup();
    show(first.spec, { readBy: "model" });
    expect(screen.getByText(CHIPS.readBy.model)).toBeInTheDocument();

    cleanup();
    show(meta.defaults.rent, { readBy: null });
    expect(screen.queryByText(CHIPS.readBy.rule)).toBeNull();
    expect(screen.queryByText(CHIPS.readBy.model)).toBeNull();
  });

  test("test_a_refusal_is_said_in_the_chip_it_concerns", async () => {
    const { user } = show(first.spec, { refused: new Map<string, RejectReason>([["place:syn-p0021", "out_of_range"]]) });

    await user.click(screen.getByRole("button", { name: /^Cindermoor Works/ }));

    const chip = screen.getByRole("button", { name: /^Cindermoor Works/ }).closest("li") as HTMLElement;
    expect(within(chip).getByRole("alert")).toHaveTextContent(REJECTED.out_of_range);
  });

  test("test_while_the_first_sentence_is_read_the_row_holds_its_place", () => {
    const { container } = show(meta.defaults.rent, { waiting: true, readBy: null });

    expect(container.querySelectorAll(".skeleton")).toHaveLength(3);
    expect(screen.queryAllByRole("listitem")).toEqual([]);
  });

  test("test_the_chips_have_no_accessibility_fault", async () => {
    const { container, user } = show();
    await user.click(screen.getByRole("button", { name: /^Cindermoor Works/ }));

    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_the_chips_have_no_accessibility_fault_in_a_row", async () => {
    const { container } = show(first.spec, { inARow: true });

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("the chips in the row", () => {
  const STYLES = rulesOf(readFileSync(path.join(__dirname, "ChipRow.module.css"), "utf8"));

  test("test_what_was_asked_for_stands_in_the_row_six_at_most_and_a_button_shows_the_rest", async () => {
    const { user } = show(many, { inARow: true });

    expect(SHOWN_AT_FIRST).toBe(6);
    // Five vibes and the place. The budget and the tenure wait, and the usual settings stand last.
    expect(chips().map(wordsOf)).toEqual([
      "Leafy",
      "Quiet streets",
      "Village feel",
      "Parks close by",
      "Food and drink",
      `Cindermoor Works, within 35 minutes, ${CHIPS.restAssumed}`,
      `Usual settings: 6 ${CHIPS.assumed}`,
    ]);
    const rest = screen.getByRole("button", { name: CHIPS.rest(2) });
    expect(rest).toHaveAttribute("aria-expanded", "false");

    await user.click(rest);

    expect(chips()).toHaveLength(9);
    // The button stays where it was, so that the focus is not left on nothing, and closes the row again.
    expect(screen.getByRole("button", { name: CHIPS.showFewer })).toHaveFocus();
    await user.click(screen.getByRole("button", { name: CHIPS.showFewer }));
    expect(chips()).toHaveLength(7);
  });

  test("test_with_a_budget_and_a_workplace_every_vibe_asked_for_is_still_in_the_row", () => {
    // Seen in a browser: three chips were shown, tenure, budget and place, so a vibe that was
    // asked for beside a budget and a workplace was never seen until "+N more" was pressed.
    show(first.spec, { inARow: true });

    expect(first.spec.budget.amount).not.toBeNull();
    expect(first.spec.commutes).toHaveLength(1);
    expect(chips().map(wordsOf).slice(0, 2)).toEqual(["Leafy", "Quiet streets"]);
    expect(screen.queryByRole("button", { name: /more$/ })).toBeNull();
  });

  test("test_the_usual_settings_stand_last_and_are_not_counted_among_the_six", () => {
    show(many, { inARow: true });

    expect(wordsOf(chips().at(-1) as HTMLElement)).toBe(`Usual settings: 6 ${CHIPS.assumed}`);
    expect(chips()).toHaveLength(SHOWN_AT_FIRST + 1);
  });

  test("test_in_the_row_a_chip_says_what_was_said_and_that_the_rest_was_assumed", () => {
    show(first.spec, { inARow: true });

    // One part that nobody said is named, and the word "assumed" stands on it alone. Seen
    // in a browser: "rest assumed" beside the very words that were typed.
    expect(chips().map(wordsOf)).toEqual([
      "Leafy",
      "Quiet streets",
      `Cindermoor Works, within 35 minutes, ${CHIPS.restAssumed}`,
      `£1,700 a month, One bedroom, flexible ${CHIPS.assumed}`,
      "Renting",
      `Usual settings: 6 ${CHIPS.assumed}`,
    ]);
    // The dashed edge still says that something was assumed.
    expect(chips().map((chip) => chip.getAttribute("data-assumed"))).toEqual([
      "false",
      "false",
      "true",
      "true",
      "false",
      "true",
    ]);
  });

  test("test_what_explains_the_chips_is_drawn_once_the_row_is_opened_out", async () => {
    const { user } = show(many, { inARow: true });
    expect(screen.queryByText(CHIPS.assumedHint)).toBeNull();

    await user.click(screen.getByRole("button", { name: CHIPS.rest(2) }));

    expect(canBeSeen(screen.getByText(CHIPS.assumedHint))).toBe(true);
    expect(canBeSeen(screen.getByText(`${CHIPS.usualHint} ${CHIPS.openSettings}`))).toBe(true);
  });

  test("test_a_chip_that_is_opened_opens_the_row_out_so_that_it_is_drawn_in_full", async () => {
    const { user } = show(many, { inARow: true });

    await user.click(screen.getByRole("button", { name: /^Cindermoor Works/ }));

    expect(chips()).toHaveLength(9);
    expect(chips().map(wordsOf)).toContain(
      "Cindermoor Works, Public transport assumed, within 35 minutes, flexible assumed",
    );
    expect(screen.getByRole("group", { name: JOURNEY.place("Cindermoor Works") })).toBeInTheDocument();
    // While a chip is open the button that closes the row does nothing, and says so.
    expect(screen.getByRole("button", { name: CHIPS.showFewer })).toHaveAttribute("aria-disabled", "true");
  });

  test("test_with_few_chips_there_is_no_button_and_they_are_said_in_short_all_the_same", () => {
    show(meta.defaults.rent, { assumed: {}, readBy: null, inARow: true });

    expect(chips()).toHaveLength(2);
    expect(chips().map((chip) => chip.textContent)).toEqual([`Renting ${CHIPS.assumed}`, `Usual settings: 6 ${CHIPS.assumed}`]);
    expect(screen.queryByRole("button", { name: /more$/ })).toBeNull();
    // Seen in a browser: three chips in full took three lines of a phone, and the first
    // result began below its first screen.
    expect(chips()[0]?.closest("[data-out]")).toHaveAttribute("data-out", "false");
  });

  test("test_a_few_chips_are_explained_when_one_of_them_is_opened_and_not_before", async () => {
    // Seen in a browser: a search for one vibe, from the shelf, had three chips and two lines
    // that explained them, and its first result began below the first screen of a phone.
    const { user } = show(meta.defaults.rent, { assumed: {}, readBy: null, inARow: true });
    expect(screen.queryByText(CHIPS.assumedHint)).toBeNull();
    expect(screen.queryByText(CHIPS.usualHint, { exact: false })).toBeNull();

    await user.click(screen.getByRole("button", { name: /^Renting/ }));

    expect(canBeSeen(screen.getByText(CHIPS.assumedHint))).toBe(true);
    expect(canBeSeen(screen.getByText(`${CHIPS.usualHint} ${CHIPS.openSettings}`))).toBe(true);
  });

  test("test_the_chips_wrap_and_nothing_of_a_chip_is_cut_off_or_scrolled_out_of_sight", () => {
    // Seen in a browser: the chips stood on one line that scrolled sideways with no sign that
    // it did. On a desk the workplace read "Cindermoor", which is the name of an area. On a
    // phone it was off the screen, and 21 px of "Turn" showed.
    const setBy = (property: string) => STYLES.map((rule) => rule.sets.get(property)).filter((value) => value !== undefined);

    expect(STYLES.filter((rule) => isFor(rule.selector, "chips")).map((rule) => rule.sets.get("flex-wrap"))).toContain("wrap");
    expect(setBy("flex-wrap")).not.toContain("nowrap");
    expect(setBy("white-space")).toEqual([]);
    expect(setBy("text-overflow")).toEqual([]);
    expect([...setBy("overflow"), ...setBy("overflow-x")]).toEqual([]);
    // A chip is never wider than the row, so that a long name goes onto a second line inside it.
    for (const part of ["chip", "head"]) {
      expect(STYLES.filter((rule) => isFor(rule.selector, part)).map((rule) => rule.sets.get("max-width"))).toContain("100%");
    }
  });

  test("test_turn_and_the_way_out_keep_their_width_so_that_each_is_whole_and_can_be_pressed", () => {
    // The words of a chip give way. What is pressed beside them does not.
    const beside = STYLES.filter((rule) => rule.under === null && (isFor(rule.selector, "turn") || isFor(rule.selector, "remove")));

    expect(beside.map((rule) => rule.sets.get("flex"))).toContain("none");
    expect(new Set(beside.filter((rule) => rule.sets.has("flex")).map((rule) => subjectOf(rule.selector)))).toEqual(
      new Set([".turn", ".remove"]),
    );
  });
});

describe("a chip of a vibe", () => {
  const calm = recordedAnswer("interpret", "interpret-scale").body.data;
  const turned = recordedAnswer("rank", "rank-scale-turned");

  test("test_a_scale_says_which_end_is_asked_for", () => {
    show(calm.spec, { assumed: {} });

    expect(chips().map((chip) => chip.textContent?.replace(/×|Turn/g, ""))).toContain(CHIPS.towards("Going out", "Calm"));
  });

  test("test_turn_asks_for_the_other_end_in_the_edit_the_api_was_recorded_taking", async () => {
    const { user, sent } = show(calm.spec, { assumed: {} });

    await user.click(screen.getByRole("button", { name: CHIPS.turnTo("Going out", "Buzzy") }));

    expect(screen.getByRole("button", { name: CHIPS.turnTo("Going out", "Buzzy") })).toHaveTextContent(CHIPS.turn);
    expect(sent).toEqual([(turned.request.body as { operations: Operations }).operations]);
  });

  test("test_once_turned_the_chip_names_the_other_end_and_turn_leads_back", () => {
    show(turned.body.data.spec, { assumed: {} });

    expect(chips().map((chip) => chip.textContent?.replace(/×|Turn/g, ""))).toContain(CHIPS.towards("Going out", "Buzzy"));
    expect(screen.getByRole("button", { name: CHIPS.turnTo("Going out", "Calm") })).toBeInTheDocument();
  });

  test("test_a_vibe_that_runs_one_way_has_nothing_to_turn", () => {
    show();

    expect(screen.queryByRole("button", { name: /^Turn/ })).toBeNull();
  });

  test("test_a_chip_of_a_scale_opens_one_slider_with_both_ends_named", async () => {
    const { user, sent } = show(calm.spec, { assumed: {} });

    await user.click(screen.getByRole("button", { name: new RegExp(`^${CHIPS.towards("Going out", "Calm")}`) }));
    const slider = screen.getByRole("slider", { name: "Going out" });

    expect(slider).toHaveAttribute("min", "-100");
    expect(slider).toHaveAttribute("max", "100");
    expect(slider).toHaveValue("-50");
    await user.click(screen.getByRole("button", { name: SLIDER.toward("Going out", "Buzzy") }));
    expect(sent).toEqual([]);
  });

  test("test_a_word_with_two_meanings_is_quoted_and_marked_assumed", () => {
    const gritty = recordedAnswer("interpret", "variant-a/interpret-gritty").body.data;
    const form = recordedAnswer("get_meta", "variant-a/meta").body.data;
    const key = "tag:works_warehouses";
    show(gritty.spec, { form, assumed: { [key]: ["weight", "word"] }, quoted: { [key]: "gritty" } });

    const chip = chips().find((one) => one.textContent?.startsWith("Works and warehouses"));
    // It is said in the row, as the chips first stand, and is never left for a press.
    expect(chip?.closest("[data-out]")).toHaveAttribute("data-out", "false");
    expect(chip?.textContent?.replace("×", "")).toBe(
      `Works and warehouses, ${CHIPS.readFrom("gritty")} ${CHIPS.assumed}`,
    );
    expect(chip).toHaveAttribute("data-assumed", "true");
  });
});
