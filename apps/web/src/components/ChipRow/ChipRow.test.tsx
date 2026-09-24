import { readFileSync } from "node:fs";
import path from "node:path";

import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { COMBINE } from "@/content/labels";
import { CHIPS, PLACE, REJECTED, TENURE_CHOICE } from "@/content/search";
import { BUDGET, JOURNEY } from "@/content/settings";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Operations, PreferenceSpec, RejectReason, Tenure } from "@/lib/api/schema";
import { edits } from "@/lib/search/edits";
import type { Assumed } from "@/lib/search/state";

import { faultsIn } from "../../../test/support/axe";
import { ChipRow } from "./ChipRow";

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const first = recordedAnswer("interpret", "interpret-first").body.data;
const two = recordedAnswer("interpret", "interpret-two-journeys").body.data;
const ASSUMED: Assumed = { budget: ["strictness"], "place:syn-p0021": ["mode", "strictness"] };

/** True when the words are drawn where a person who sees the page can read them. */
const canBeSeen = (element: HTMLElement) =>
  element.closest(".visually-hidden, [aria-hidden='true'], [hidden]") === null;

function show(
  spec: PreferenceSpec = first.spec,
  {
    assumed = ASSUMED,
    refused,
    waiting = false,
    readBy = "rule" as const,
    placeNames = { "syn-p0021": "Cindermoor Works" },
    tenureSaid = false,
  }: {
    tenureSaid?: boolean;
    assumed?: Assumed;
    refused?: ReadonlyMap<string, RejectReason>;
    waiting?: boolean;
    readBy?: "rule" | "claude" | null;
    placeNames?: Record<string, string>;
  } = {},
) {
  const sent: Operations[] = [];
  const tenures: Tenure[] = [];
  const onOpenSettings = jest.fn();
  const view = render(
    <ChipRow
      spec={spec}
      assumed={assumed}
      placeNames={placeNames}
      meta={meta}
      areas={areas}
      onEdit={(operations) => sent.push(operations)}
      onTenure={(tenure) => tenures.push(tenure)}
      onOpenSettings={onOpenSettings}
      version={1}
      refused={refused}
      readBy={readBy}
      waiting={waiting}
      tenureSaid={tenureSaid}
    />,
  );
  return { sent, tenures, onOpenSettings, user: userEvent.setup({ delay: null }), ...view };
}

const chips = () => screen.getAllByRole("listitem");
const heading = () => screen.getByRole("heading", { level: 2 });

describe("the chips", () => {
  test("test_each_part_nobody_chose_carries_the_word_assumed", () => {
    show();

    expect(chips().map((chip) => chip.textContent?.replace("×", ""))).toEqual([
      "Renting assumed",
      "£1,700 a month, One bedroom, flexible assumed",
      "Cindermoor Works, Public transport assumed, within 35 minutes, flexible assumed",
      "Leafy",
      "Quiet residential",
      expect.stringMatching(/^Usual settings: 6 assumed/),
    ]);
    // The word says it. The dashed edge repeats it for the eye.
    expect(chips().map((chip) => chip.getAttribute("data-assumed"))).toEqual([
      "true",
      "true",
      "true",
      "false",
      "false",
      "true",
    ]);
  });

  test("test_a_tenure_the_person_said_does_not_carry_the_word_assumed", () => {
    show(first.spec, { tenureSaid: true });

    expect(chips()[0]?.textContent).toBe("Renting");
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
    expect(screen.getByRole("button", { name: /^Quiet residential/ })).toHaveFocus();
  });

  test("test_removing_the_last_chip_that_can_be_removed_moves_the_focus_to_a_chip_that_stays", async () => {
    const { user } = show({ ...first.spec, weights: first.spec.weights.filter((weight) => weight.provenance !== "default") });
    const last = screen.getByRole("button", { name: `${CHIPS.remove}: Quiet residential` });
    last.focus();

    await user.keyboard("{Enter}");

    expect(document.activeElement).not.toBe(document.body);
    expect(document.activeElement).not.toBe(last);
    expect(screen.getByRole("button", { name: /^Leafy/ })).toHaveFocus();
  });

  test("test_the_chips_can_be_given_the_focus_by_the_page_and_are_no_stop_of_their_own", () => {
    show();

    // A question that is answered goes, and the focus goes to what the answer changes.
    expect(screen.getByRole("region", { name: CHIPS.label })).toHaveAttribute("tabindex", "-1");
  });

  test("test_a_chip_opens_the_control_the_settings_hold_in_place_and_one_is_open_at_a_time", async () => {
    const { user } = show();

    await user.click(screen.getByRole("button", { name: /^£1,700 a month/ }));
    expect(screen.getByRole("button", { name: /^£1,700 a month/ })).toHaveAttribute("aria-expanded", "true");
    expect(within(chips()[1] as HTMLElement).getByRole("group", { name: BUDGET.legend })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /^Cindermoor Works/ }));
    expect(screen.queryByRole("group", { name: BUDGET.legend })).toBeNull();
    expect(
      within(chips()[2] as HTMLElement).getByRole("group", { name: JOURNEY.place("Cindermoor Works") }),
    ).toBeInTheDocument();
    expect(screen.getAllByRole("button", { expanded: true })).toHaveLength(1);
  });

  test("test_the_control_in_a_chip_sends_the_same_edit_as_the_one_in_the_settings", async () => {
    const { user, sent } = show();

    await user.click(screen.getByRole("button", { name: /^£1,700 a month/ }));
    await user.click(screen.getByRole("checkbox", { name: BUDGET.firm }));
    await user.click(screen.getByRole("button", { name: /^Leafy/ }));
    await user.click(screen.getByRole("switch", { name: "Leafy" }));

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
      "Remove: £1,700 a month",
      "Remove: Cindermoor Works",
      "Remove: Leafy",
      "Remove: Quiet residential",
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
    expect(screen.getByRole("button", { name: /^Usual settings: 6/ })).toHaveAccessibleDescription(
      `${CHIPS.usualHint} ${CHIPS.openSettings}`,
    );
  });

  test("test_what_the_usual_settings_are_is_said_where_it_can_be_seen", () => {
    show();

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

  test("test_what_assumed_means_is_said_once_wherever_anything_is_marked_so", () => {
    show();
    expect(canBeSeen(screen.getByText(CHIPS.assumedHint))).toBe(true);
    expect(CHIPS.assumedHint).toContain(CHIPS.assumed);

    cleanup();
    const stated = {
      ...first.spec,
      tenure_from: "stated" as const,
      commutes: [],
      weights: first.spec.weights.filter((weight) => weight.provenance !== "default"),
    };
    show(stated, { assumed: {} });
    expect(chips().map((chip) => chip.getAttribute("data-assumed"))).not.toContain("true");
    expect(screen.queryByText(CHIPS.assumedHint)).toBeNull();
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
    const highStreet = "Share of homes within a 10-minute walk of a high street or town centre";
    const { user, sent } = show(second);

    const chip = screen.getByRole("button", { name: new RegExp(`^${highStreet}`) });
    expect(chip).toHaveTextContent(`${highStreet}, ${CHIPS.off}`);
    expect(screen.queryByRole("button", { name: `${CHIPS.remove}: ${highStreet}` })).toBeNull();
    expect(screen.getByRole("button", { name: `${CHIPS.remove}: Public green space as a share of the area` })).toBeInTheDocument();

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

  test("test_a_place_with_no_name_in_hand_is_said_to_be_one_the_website_cannot_name", () => {
    // The reading names two places by id. The website has the name of one of them.
    show(two.spec, { assumed: {}, placeNames: { "syn-p0026": "Wexmoor University" } });

    expect(two.spec.commutes.map((commute) => commute.place_id)).toEqual(["syn-p0019", "syn-p0026"]);
    expect(chips().map((chip) => chip.textContent?.replace("×", "").split(",")[0])).toEqual(
      expect.arrayContaining([PLACE.unnamed(1), "Wexmoor University"]),
    );
    const said = screen.getByText(PLACE.unnamedHint(1, 2));
    expect(canBeSeen(said)).toBe(true);
    // The number is where the data lists the place, which is not where the person said it.
    expect(PLACE.unnamedHint(1, 2)).toMatch(/not the order you named them in/);
  });

  test("test_nothing_is_said_of_names_when_every_place_has_one", () => {
    show(two.spec, {
      assumed: {},
      placeNames: { "syn-p0019": "Foxholt Market", "syn-p0026": "Wexmoor University" },
    });

    expect(screen.queryByText(/cannot show the name/)).toBeNull();

    cleanup();
    show();
    expect(screen.queryByText(/cannot show the name/)).toBeNull();
  });

  test("test_one_place_with_no_name_is_not_said_to_be_out_of_order", () => {
    show(first.spec, { placeNames: {} });

    expect(screen.getByText(PLACE.unnamedHint(1, 1))).toBeInTheDocument();
    expect(PLACE.unnamedHint(1, 1)).not.toMatch(/order/);
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
    expect(CHIPS.readBy.claude).toMatch(/by AI/);
  });

  test("test_the_line_under_the_chips_says_who_read_the_words", () => {
    show();
    expect(screen.getByText(CHIPS.readBy.rule)).toBeInTheDocument();

    cleanup();
    show(first.spec, { readBy: "claude" });
    expect(screen.getByText(CHIPS.readBy.claude)).toBeInTheDocument();

    cleanup();
    show(meta.defaults.rent, { readBy: null });
    expect(screen.queryByText(CHIPS.readBy.rule)).toBeNull();
    expect(screen.queryByText(CHIPS.readBy.claude)).toBeNull();
  });

  test("test_a_refusal_is_said_in_the_chip_it_concerns", async () => {
    const { user } = show(first.spec, { refused: new Map<string, RejectReason>([["place:syn-p0021", "out_of_range"]]) });

    await user.click(screen.getByRole("button", { name: /^Cindermoor Works/ }));

    expect(within(chips()[2] as HTMLElement).getByRole("alert")).toHaveTextContent(REJECTED.out_of_range);
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
});
