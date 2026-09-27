import { readFileSync } from "node:fs";
import path from "node:path";

import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { COMBINE } from "@/content/labels";
import { CHIPS, PLACE, REJECTED, TENURE_CHOICE } from "@/content/search";
import { BUDGET, JOURNEY, SLIDER } from "@/content/settings";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Operations, PreferenceSpec, RejectReason, Tenure } from "@/lib/api/schema";
import { chipsOf } from "@/lib/search/chips";
import { edits } from "@/lib/search/edits";
import type { Assumed } from "@/lib/search/state";

import { faultsIn } from "../../../test/support/axe";
import { asWritten } from "../../../test/support/contrast";
import { isFor, rulesOf, subjectOf } from "../../../test/support/css";
import { ROUGH, sayingSo } from "../../../test/support/rough";
import { pictureOf } from "../kit/drawings";
import { drawingOf, outlineOf } from "../kit/Thing/drawn";
import { ChipRow, SHOWN_AT_FIRST } from "./ChipRow";
import { ON_A_WIDE_SCREEN, stateOf, thingOf } from "./drawn";
import { NARROW_ROW, roomOf, WIDE_ROWS } from "./rows";

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const first = recordedAnswer("interpret", "interpret-first").body.data;
const two = recordedAnswer("interpret", "interpret-two-journeys").body.data;
const ASSUMED: Assumed = { budget: ["strictness"], "place:syn-p0021": ["mode", "strictness"] };
const PLACES = { "syn-p0021": "Cindermoor Works" };

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
  art?: "screen" | "small";
}

function show(
  spec: PreferenceSpec = first.spec,
  {
    assumed = ASSUMED,
    refused,
    waiting = false,
    readBy = "rule" as const,
    placeNames = PLACES,
    tenurePicked = false,
    quoted = {},
    form = meta,
    inARow = false,
    art,
  }: Shown = {},
) {
  const sent: Operations[] = [];
  const tenures: Tenure[] = [];
  const view = render(
    <ChipRow
      spec={spec}
      assumed={assumed}
      placeNames={placeNames}
      meta={form}
      areas={areas}
      onEdit={(operations) => sent.push(operations)}
      onTenure={(tenure) => tenures.push(tenure)}
      version={1}
      refused={refused}
      readBy={readBy}
      waiting={waiting}
      tenurePicked={tenurePicked}
      quoted={quoted}
      art={art}
    />,
  );
  // Most of what is held here is of the chips in full, which are one press away.
  const rest = screen.queryByRole("button", { name: /^\+\d+ more$/ });
  if (!inARow && rest !== null) fireEvent.click(rest);
  return { sent, tenures, user: userEvent.setup({ delay: null }), ...view };
}

const chips = () => screen.getAllByRole("listitem");
const heading = () => screen.getByRole("heading", { level: 2 });
/** What a chip says of itself: its words, and not what it opens to nor its way out. */
const wordsOf = (chip: HTMLElement) => (chip.querySelector("[data-main]") ?? chip.querySelector("span"))?.textContent ?? "";
/** The picture that is drawn beside the words of a chip, by where it is served from. */
const drawnIn = (chip: HTMLElement) =>
  /^url\("(.+)"\)$/.exec(chip.querySelector<HTMLElement>(".drawing")?.style.getPropertyValue("--art") ?? "")?.[1] ?? null;
/** The state a chip is drawn in: by its edge, and by its thing. */
const stateIn = (chip: HTMLElement) => chip.querySelector("[data-state]")?.getAttribute("data-state") ?? null;
/** Which chips are drawn as having this moment been added. */
const arriving = () => chips().map((chip) => chip.querySelector("[data-arrives]")?.getAttribute("data-arrives") === "true");
/** A search that no row has drawn: the same search, as the answer to the next press brings it. */
const anew = (spec: PreferenceSpec): PreferenceSpec => ({ ...spec });
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
      "Cindermoor Works, public transport assumed, 35 minutes, flexible assumed",
      "£1,700 a month, one bedroom, flexible assumed",
      "Renting",
    ]);
    // The word says it, and the chip says it to whatever lays the row out.
    expect(chips().map((chip) => chip.getAttribute("data-assumed"))).toEqual([
      "false",
      "false",
      "true",
      "true",
      "false",
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

  test.each([
    ["a search that words were read into", first.spec],
    ["a search of many things", many],
    ["what a search starts from", meta.defaults.rent],
    ["a search of two journeys", two.spec],
  ])("test_the_settings_nobody_chose_are_no_chip_of_the_row: %s", async (_, spec) => {
    // A person who walked the website did not know what "Usual settings: 6 assumed" was of.
    // A usual setting that nobody chose moves no area, so the chip told them nothing they
    // could use. Every setting stands with its value where the search is refined.
    const { container, user } = show(spec);
    const held = chipsOf(spec, meta, areas, PLACES, ASSUMED);

    // The search holds them still, and no chip is made of them: the row draws every chip there is.
    expect(spec.weights.filter((weight) => weight.provenance === "default").length).toBeGreaterThan(0);
    expect(held.map((chip) => chip.key).filter((key) => /usual/i.test(key))).toEqual([]);
    expect(chips().map((chip) => chip.textContent ?? "").filter((words) => /usual/i.test(words))).toEqual([]);
    expect(chips().length).toBeGreaterThanOrEqual(held.length);
    // Nor is anything said of them to whoever hears the row: no name, and no description.
    await user.click(screen.getByRole("button", { name: /^(Renting|Buying)/ }));
    expect(/usual settings/i.test(container.textContent ?? "")).toBe(false);
    for (const button of screen.getAllByRole("button")) {
      expect(/usual/i.test(button.getAttribute("aria-label") ?? "")).toBe(false);
      expect(button).not.toHaveAttribute("aria-describedby");
    }
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
    // It is the journey that does least well against its own limit, which need not be the
    // one that takes the most minutes. "The slowest" would be untrue of it.
    const contract = readFileSync(path.resolve(__dirname, "../../../../../docs/design/contract.md"), "utf8");

    expect(contract).toContain("`slowest`, the default, takes the `min` of the destinations' utilities");
    expect(COMBINE.slowest).toMatch(/least well against its limit/);
    expect(COMBINE.slowest).not.toMatch(/slowest/);
  });

  test.each(["rule", "model", null] as const)(
    "test_the_plate_says_what_the_chips_are_and_nothing_of_who_read_the_words: %s",
    async (readBy) => {
      // A person who walked the website asked for the label beside the heading to go: it said
      // that rules had read the words, or that a language model had. Whether a language model
      // reads what is typed is said under the box, where the privacy notice promises it.
      const { container, user } = show(first.spec, { readBy });
      const plate = heading().closest("p") as HTMLElement;

      // Words that were read make what was understood, whoever read them.
      expect(plate.textContent).toBe(readBy === null ? CHIPS.setLabel : CHIPS.label);
      expect([...plate.children]).toEqual([heading()]);
      // Nor is it said once the row is opened out, among what explains the chips.
      await user.click(screen.getByRole("button", { name: /^Renting/ }));
      expect(/\bAI\b|language model|\brules?\b/i.test(container.textContent ?? "")).toBe(false);
    },
  );

  test("test_no_rule_of_the_row_draws_a_label_beside_its_heading", () => {
    const own = rulesOf(readFileSync(path.join(__dirname, "ChipRow.module.css"), "utf8"));

    expect(own.filter((rule) => /readBy/i.test(rule.selector)).map((rule) => rule.selector)).toEqual([]);
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
    // What holds a place says nothing to whoever hears the page.
    expect(container.querySelector(".skeleton")?.closest("[aria-hidden='true']")).not.toBeNull();
  });

  test("test_no_edge_of_the_row_is_drawn_in_dashes_or_in_dots_nor_of_what_holds_the_place_of_a_chip", () => {
    // A person who walked the website did not know what a dashed edge was for. What holds
    // the place of a chip had one too: it is the row's own now, within a solid edge.
    const written = readFileSync(path.join(__dirname, "ChipRow.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
    const own = rulesOf(written);

    expect(/dashed|dotted|repeating-linear-gradient/.test(written)).toBe(false);
    expect(own.filter((rule) => rule.sets.get("border-color") === "transparent").map((rule) => rule.selector)).toEqual([]);
    expect(own.filter((rule) => rule.under === null && rule.selector === ".held").map((rule) => rule.sets.get("border"))).toEqual([
      "var(--edge) solid var(--border)",
    ]);
    const { container } = show(meta.defaults.rent, { waiting: true, readBy: null });
    expect([...container.querySelectorAll(".skeleton")].map((held) => held.className)).toEqual([
      "skeleton held",
      "skeleton held",
      "skeleton held",
    ]);
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

describe("a chip as it is drawn", () => {
  const second = recordedAnswer("interpret", "interpret-second-sentence").body.data.spec;

  test("test_each_chip_has_the_drawing_of_its_thing_beside_its_words_chosen_by_what_the_service_gives", () => {
    show(many);
    const held = chipsOf(many, meta, areas, PLACES, ASSUMED);

    // By the id of its vibe where that is drawn, else by its family, else the plain one: and
    // by its kind where it is no vibe. Which is which is the kit's to say, and no name is written here.
    expect(chips().map(drawnIn)).toEqual(
      held.map((chip) => pictureOf(drawingOf(thingOf(chip, meta)))),
    );
    expect(new Set(chips().map(drawnIn)).size).toBeGreaterThan(5);
    // The drawing is dress. It stands before the words, and says nothing to whoever hears the page.
    for (const chip of chips()) {
      const drawing = chip.querySelector(".drawing");
      expect(drawing?.closest("[aria-hidden='true']")).not.toBeNull();
      expect(drawing?.compareDocumentPosition(chip.querySelector(".words") as Element)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
    }
    expect(screen.queryByRole("img")).toBeNull();
  });

  test("test_the_id_of_a_place_is_in_nothing_that_is_drawn", () => {
    const { container } = show();

    expect(first.spec.commutes.map((commute) => commute.place_id)).toEqual(["syn-p0021"]);
    expect(container.innerHTML.includes("syn-p0021")).toBe(false);
  });

  test("test_what_nobody_said_bears_the_word_once_for_each_part_of_it_and_what_a_person_said_does_not", () => {
    show(first.spec, { inARow: true });
    const held = chipsOf(first.spec, meta, areas, PLACES, ASSUMED);

    expect(chips().map(stateIn)).toEqual(["said", "said", "assumed", "assumed", "said"]);
    expect(chips().map(stateIn)).toEqual(held.map((chip) => stateOf(chip, first.spec)));
    // The word says it, once for each part that nobody said and no more: the part of the
    // kit is told that the words of the chip do, and says nothing of its own.
    const parts = (at: number) => held[at]?.parts.filter((part) => part.assumed).length ?? 0;
    expect(chips().map((chip) => wordsOf(chip).split(CHIPS.assumed).length - 1)).toEqual(held.map((_, at) => parts(at)));
    expect(held.map((_, at) => parts(at))).toEqual([0, 0, 2, 1, 0]);
    for (const chip of chips().filter((one) => stateIn(one) === "said")) {
      expect(wordsOf(chip)).not.toContain(CHIPS.assumed);
    }
  });

  test("test_what_counts_for_nothing_has_its_thing_in_outline_and_says_so_once", () => {
    show(second);
    const off = chipsOf(second, meta, areas, PLACES, {}).filter((chip) => stateOf(chip, second) === "off");
    const drawn = chips().filter((chip) => stateIn(chip) === "off");

    expect(off).toHaveLength(1);
    expect(drawn.map(wordsOf)).toEqual(off.map((chip) => `${chip.label}, ${CHIPS.off}`));
    // Its own drawing, with the colour taken off it.
    const [thing] = off.map((chip) => drawingOf(thingOf(chip, meta)));
    const outline = thing === undefined ? null : outlineOf(thing);
    expect(outline).not.toBeNull();
    expect(drawn.map(drawnIn)).toEqual([outline === null ? null : pictureOf(outline)]);
    // Every other chip of the search is drawn in colour.
    expect(chips().filter((chip) => stateIn(chip) !== "off").map(drawnIn).filter((picture) => picture?.endsWith("-off.png"))).toEqual([]);
  });

  test("test_the_cross_is_a_button_of_its_own_the_size_of_a_main_control_and_the_drawing_of_a_cross", () => {
    show();

    for (const cross of screen.getAllByRole("button", { name: /^Remove: / })) {
      expect(cross.tagName).toBe("BUTTON");
      expect(cross).toHaveClass("target");
      expect(cross.textContent).toBe("");
      expect(cross.querySelector<HTMLElement>("[aria-hidden='true']")?.style.getPropertyValue("--art")).toBe(
        `url("${pictureOf("ui-cross")}")`,
      );
    }
    // The part of the kit draws it 44 px wide, in a chip that is 44 px high at the least.
    const kit = rulesOf(readFileSync(path.join(__dirname, "../kit/Label/Label.module.css"), "utf8"));
    const setBy = (selector: string, property: string) => kit.filter((rule) => rule.selector === selector).map((rule) => rule.sets.get(property));
    expect(setBy(".off", "width")).toContain("var(--target)");
    expect(setBy(".off", "flex")).toContain("none");
    expect(setBy(".chip", "min-height")).toContain("var(--target)");
  });

  test("test_the_control_a_chip_opens_stands_under_it_in_the_box_that_is_in_hand", async () => {
    const { user } = show();
    const chip = screen.getByRole("button", { name: /^£1,700 a month/ });
    const opened = () => document.getElementById(chip.getAttribute("aria-controls") ?? "");

    // It is there before it is opened, so that the chip can say what it opens, and holds nothing.
    expect(opened()).toHaveAttribute("hidden");
    expect(opened()?.textContent).toBe("");

    await user.click(chip);

    expect(opened()).not.toHaveAttribute("hidden");
    expect(opened()).toHaveAttribute("data-kind", "box-on");
    expect(opened()?.closest("li")).toBe(chip.closest("li"));
    expect(chip.compareDocumentPosition(opened() as Element)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
    expect(within(opened() as HTMLElement).getByRole("group", { name: BUDGET.legend })).toBeInTheDocument();
  });

  test("test_the_button_that_shows_the_rest_says_whether_the_row_is_opened_out_and_is_the_size_of_a_main_control", async () => {
    const { user } = show(many, { inARow: true });
    const rest = screen.getByRole("button", { name: CHIPS.rest(2) });

    expect(rest.tagName).toBe("BUTTON");
    expect(rest).toHaveClass("target");
    expect(rest).toHaveAttribute("aria-expanded", "false");

    await user.click(rest);
    expect(rest).toHaveAccessibleName(CHIPS.showFewer);
    expect(rest).toHaveAttribute("aria-expanded", "true");
    expect(rest).not.toHaveAttribute("aria-disabled");
  });
});

describe("a chip that has just been added", () => {
  /** The row, drawn for a search, to be drawn again for the next. */
  const row = (spec: PreferenceSpec, waiting = false) => (
    <ChipRow
      spec={spec}
      assumed={ASSUMED}
      placeNames={PLACES}
      meta={meta}
      areas={areas}
      onEdit={() => undefined}
      onTenure={() => undefined}
      version={1}
      readBy="rule"
      waiting={waiting}
    />
  );
  /** What the part of the kit says when a chip has dropped into its place. */
  const dropped = (chip: HTMLElement) => fireEvent.animationEnd(chip.querySelector("[data-arrives]") as Element);
  /** A vibe the search does not hold, whichever the release has, asked for as a word asks for one. */
  const spare = meta.tags.find((tag) => !first.spec.tags.some((one) => one.tag_id === tag.tag_id));
  const added = { tag_id: spare?.tag_id ?? "leafy", weight: 0.5, toward: "high", provenance: "stated" } as const;

  /** Every chip of the row has dropped, each saying so for itself. */
  const allDropped = () => chips().forEach(dropped);

  test("test_each_chip_lands_for_itself_so_that_one_landing_does_not_cut_another_short", () => {
    render(row(anew(first.spec)));
    expect(arriving()).toEqual([true, true, true, true, true]);

    dropped(chips()[1] as HTMLElement);

    expect(arriving()).toEqual([true, false, true, true, true]);
  });

  test("test_it_arrives_and_no_chip_that_was_there_moves", () => {
    const was = anew(first.spec);
    const { rerender } = render(row(was));
    allDropped();
    expect(arriving()).toEqual([false, false, false, false, false]);

    rerender(row({ ...was, tags: [...was.tags, added] }));

    // The vibe that was added stands third, after the two that were there.
    expect(spare).toBeDefined();
    expect(chips().map(wordsOf)[2]?.startsWith(spare?.label ?? "no vibe to add")).toBe(true);
    expect(arriving()).toEqual([false, false, true, false, false, false]);
  });

  test("test_it_arrives_once_and_is_new_no_longer_when_it_has_dropped", () => {
    const was = anew(first.spec);
    const next = { ...was, tags: [...was.tags, added] };
    const { rerender } = render(row(was));
    allDropped();
    rerender(row(next));
    expect(arriving()).toContain(true);

    dropped(chips()[2] as HTMLElement);
    expect(arriving()).not.toContain(true);

    // Drawn again for the same search, as it is whenever anything on the page changes.
    rerender(row(next));
    expect(arriving()).not.toContain(true);
  });

  test("test_what_comes_of_a_first_sentence_arrives_where_the_row_held_its_place", () => {
    const { rerender } = render(row(anew(meta.defaults.rent), true));
    expect(screen.queryAllByRole("listitem")).toEqual([]);

    rerender(row(anew(first.spec)));

    expect(arriving()).toEqual([true, true, true, true, true]);
  });

  test("test_a_chip_that_is_taken_off_brings_nothing_down", () => {
    const was = anew(first.spec);
    const { rerender } = render(row(was));
    allDropped();

    rerender(row({ ...was, tags: was.tags.slice(1) }));

    expect(chips()).toHaveLength(4);
    expect(arriving()).not.toContain(true);
  });

  test("test_a_search_that_is_drawn_a_second_time_brings_nothing_down", () => {
    // As when a person comes back to the page from the page of an area: the search is the
    // one the page held, and its chips were there.
    const held = anew(first.spec);
    const once = render(row(held));
    expect(arriving()).toEqual([true, true, true, true, true]);
    once.unmount();

    render(row(held));

    expect(arriving()).not.toContain(true);
  });

  test("test_a_search_that_no_row_has_drawn_arrives_whole", () => {
    // As when a word of the shelf opens a search: the row is first drawn with the chip in it.
    render(row(anew(first.spec)));

    expect(arriving()).toEqual([true, true, true, true, true]);
  });

  test("test_opening_the_row_out_brings_nothing_down_though_a_chip_is_drawn_that_was_not_in_sight", async () => {
    const user = userEvent.setup({ delay: null });
    render(row(anew(many)));
    expect(chips()).toHaveLength(SHOWN_AT_FIRST);
    expect(arriving()).not.toContain(false);

    // Where less movement is asked for nothing drops, and nothing says that it has. The
    // press is what settles the row.
    await user.click(screen.getByRole("button", { name: CHIPS.rest(2) }));

    expect(chips()).toHaveLength(8);
    expect(arriving()).not.toContain(true);
  });

  test("test_opening_a_chip_brings_nothing_down", async () => {
    const user = userEvent.setup({ delay: null });
    render(row(anew(first.spec)));

    await user.click(screen.getByRole("button", { name: /^Renting/ }));

    expect(arriving()).not.toContain(true);
  });

  test("test_how_it_drops_is_the_kits_and_nothing_of_the_row_moves", () => {
    const own = rulesOf(readFileSync(path.join(__dirname, "ChipRow.module.css"), "utf8"));
    const moving = own.filter((rule) => [...rule.sets.keys()].some((property) => /^(animation|transition|transform|translate)/.test(property)));

    expect(moving.map((rule) => rule.selector)).toEqual([]);
    expect(readFileSync(path.join(__dirname, "ChipRow.module.css"), "utf8")).not.toMatch(/@keyframes/);
  });
});

describe("what Burro took for the person", () => {
  // The page asks nothing: where a sentence could be taken two ways, Burro takes one, and
  // the chip of what it took says that it was assumed. A chip can be taken off, or changed.
  const TAKEN: Assumed = { budget: ["strictness"], "place:syn-p0021": ["mode", "strictness", "place"] };

  test("test_a_place_that_was_the_first_of_several_says_assumed_after_its_name_in_the_row_and_in_full", async () => {
    const { user } = show(first.spec, { assumed: TAKEN, inARow: true });
    const place = () => chips().map(wordsOf).find((words) => words.startsWith("Cindermoor Works"));

    // In the row: the name, that it was assumed, and every part, with which of them nobody chose.
    const said = `Cindermoor Works ${CHIPS.assumed}, public transport ${CHIPS.assumed}, 35 minutes, flexible ${CHIPS.assumed}`;
    expect(place()).toBe(said);

    await user.click(screen.getByRole("button", { name: /^Cindermoor Works/ }));

    // In full it says the same.
    expect(place()).toBe(said);
    // It can be taken off, as any place can, and what "assumed" means is said in sight.
    expect(screen.getByRole("button", { name: `${CHIPS.remove}: Cindermoor Works` })).toBeInTheDocument();
    expect(screen.getByText(CHIPS.assumedHint)).toBeInTheDocument();
  });

  test("test_a_place_a_person_named_in_full_says_nothing_of_the_kind_after_its_name", () => {
    show(first.spec, { inARow: true });

    expect(chips().map(wordsOf)).toContain(
      `Cindermoor Works, public transport ${CHIPS.assumed}, 35 minutes, flexible ${CHIPS.assumed}`,
    );
  });

  test("test_a_thing_that_was_taken_the_gentler_way_says_which_way_and_that_it_was_assumed", () => {
    // "Pubs are so noisy": the thing was named, and whether more or fewer was not said.
    const pubs: PreferenceSpec = {
      ...first.spec,
      tags: [],
      weights: [
        ...first.spec.weights,
        { feature_id: "venue_evening_per_homes", weight: 0.5, direction: "more", provenance: "ui_edit" },
      ],
    };
    show(pubs, { assumed: { "feature:venue_evening_per_homes": ["weight", "direction"] }, inARow: true });
    const name = meta.features.find((one) => one.feature_id === "venue_evening_per_homes")?.short_label ?? "";

    expect(chips().map(wordsOf)[0]).toBe(`${name}, ${CHIPS.more} ${CHIPS.assumed}`);
    expect(stateIn(chips()[0] as HTMLElement)).toBe("assumed");
  });
});

describe("a search for somewhere to stay", () => {
  const visiting: PreferenceSpec = { ...first.spec, tenure: "visit", tenure_from: "stated" };

  test("test_the_row_says_visiting_and_draws_no_chip_of_a_budget_or_a_home", () => {
    show(visiting, { assumed: {} });

    expect(chips().map(wordsOf)).toEqual(["Leafy", "Quiet streets", "Cindermoor Works, public transport, 35 minutes, flexible", "Visiting"]);
    expect(document.body.textContent).not.toMatch(/£|bedroom|a month/i);
  });

  test("test_the_chip_of_visiting_cannot_be_taken_off_and_says_assumed_where_nobody_said_it", () => {
    show({ ...visiting, tenure_from: "default" }, { assumed: {} });

    expect(chips().map(wordsOf).at(-1)).toBe(`Visiting ${CHIPS.assumed}`);
    expect(screen.queryByRole("button", { name: `${CHIPS.remove}: Visiting` })).toBeNull();
  });
});

describe("a vibe the service holds less sure than the rest, in a search", () => {
  // The founder walked the website and wrote: "remove the concept of rough guide, we don't
  // want to pass this on to a user". The label on the chip went, and the sentence under the
  // row that said why. The service says still which vibe it is, in a code, and no word more.
  // What it said of it until it stopped a service may say again: so the row is handed the
  // release as such a service gave it, with both laid on it, and says none of it.
  const told = sayingSo(meta);
  const asked = (tagId: "village_feel" | "parks_close_by", weight = 0.5): PreferenceSpec => ({
    ...first.spec,
    tags: [{ tag_id: tagId, weight, toward: "high", provenance: "stated" }],
  });
  const said = () => document.body.textContent ?? "";

  test("test_its_chip_is_as_the_chip_of_any_vibe_and_nothing_under_the_row_says_how_sure_it_is", async () => {
    const { user } = show(asked("village_feel"), { inARow: true, form: told });

    expect(ROUGH.tag_id).toBe("village_feel");
    expect([meta.tags.find((tag) => tag.tag_id === ROUGH.tag_id)?.sureness, told.rough_guides]).toEqual(["rough_guide", [ROUGH]]);
    expect(chips().map(wordsOf)[0]).toBe("Village feel");
    expect(said().includes(ROUGH.label)).toBe(false);
    expect(said().includes(ROUGH.why)).toBe(false);
    expect(document.querySelectorAll("[data-rough-guide]")).toHaveLength(0);

    // Nor once the row is opened out, and nor beside the slider that the chip opens.
    await user.click(screen.getByRole("button", { name: /^Village feel/ }));

    expect(screen.getByRole("button", { name: /^Village feel/ })).toHaveAttribute("aria-expanded", "true");
    expect(said().includes(ROUGH.label)).toBe(false);
    expect(said().includes(ROUGH.why)).toBe(false);
    expect(/rough guide|less sure/i.test(said())).toBe(false);
    expect(document.querySelectorAll("[data-rough-guide]")).toHaveLength(0);
  });

  test("test_the_row_reads_nothing_of_what_the_service_says_of_how_sure_a_vibe_is", () => {
    const source = ["ChipRow.tsx", "says.ts", "drawn.ts", "rows.ts"].map((file) => readFileSync(path.join(__dirname, file), "utf8"));
    const chipsSource = readFileSync(path.resolve(__dirname, "../../lib/search/chips.ts"), "utf8");

    for (const file of [...source, chipsSource]) {
      expect(file).not.toMatch(/\brough\b|rough_guides|sureness|RoughGuide/i);
    }
  });
});

describe("the chips in the row", () => {
  const STYLES = rulesOf(readFileSync(path.join(__dirname, "ChipRow.module.css"), "utf8"));
  /** The part of the kit that draws a chip: its thing, its words and its cross. */
  const KIT = rulesOf(readFileSync(path.join(__dirname, "../kit/Label/Label.module.css"), "utf8"));

  test("test_what_was_asked_for_stands_in_the_row_six_at_most_and_a_button_shows_the_rest", async () => {
    const { user } = show(many, { inARow: true });

    expect(SHOWN_AT_FIRST).toBe(6);
    // Five vibes and the place. The budget and the tenure wait.
    expect(chips().map(wordsOf)).toEqual([
      "Leafy",
      "Quiet streets",
      "Village feel",
      "Parks close by",
      "Food and drink",
      `Cindermoor Works, public transport ${CHIPS.assumed}, 35 minutes, flexible ${CHIPS.assumed}`,
    ]);
    const rest = screen.getByRole("button", { name: CHIPS.rest(2) });
    expect(rest).toHaveAttribute("aria-expanded", "false");

    await user.click(rest);

    expect(chips()).toHaveLength(8);
    // The button stays where it was, so that the focus is not left on nothing, and closes the row again.
    expect(screen.getByRole("button", { name: CHIPS.showFewer })).toHaveFocus();
    await user.click(screen.getByRole("button", { name: CHIPS.showFewer }));
    expect(chips()).toHaveLength(6);
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

  test("test_the_row_holds_six_chips_and_no_seventh_stands_after_them", () => {
    show(many, { inARow: true });

    // The chip of the settings nobody chose stood last, over and above the six.
    expect(wordsOf(chips().at(-1) as HTMLElement)).toBe(
      `Cindermoor Works, public transport ${CHIPS.assumed}, 35 minutes, flexible ${CHIPS.assumed}`,
    );
    expect(chips()).toHaveLength(SHOWN_AT_FIRST);
  });

  test("test_in_the_row_a_chip_says_every_part_of_what_was_taken_and_marks_what_was_assumed_of_it", () => {
    show(first.spec, { inARow: true });

    // Every part is named, and the word "assumed" stands on each that nobody said and on
    // no other. Seen in a browser: "rest assumed" beside the very words that were typed,
    // and then "Burro assumed the rest" of a journey, which did not say that its limit
    // was flexible.
    expect(chips().map(wordsOf)).toEqual([
      "Leafy",
      "Quiet streets",
      `Cindermoor Works, public transport ${CHIPS.assumed}, 35 minutes, flexible ${CHIPS.assumed}`,
      `£1,700 a month, one bedroom, flexible ${CHIPS.assumed}`,
      "Renting",
    ]);
    expect(document.body.textContent?.includes(CHIPS.restAssumed)).toBe(false);
    // The chip says still that something of it was assumed, to whatever lays the row out.
    expect(chips().map((chip) => chip.getAttribute("data-assumed"))).toEqual([
      "false",
      "false",
      "true",
      "true",
      "false",
    ]);
  });

  test("test_what_explains_the_chips_is_drawn_once_the_row_is_opened_out", async () => {
    const { user } = show(many, { inARow: true });
    expect(screen.queryByText(CHIPS.assumedHint)).toBeNull();

    await user.click(screen.getByRole("button", { name: CHIPS.rest(2) }));

    expect(canBeSeen(screen.getByText(CHIPS.assumedHint))).toBe(true);
  });

  test("test_a_chip_that_is_opened_opens_the_row_out_so_that_it_is_drawn_in_full", async () => {
    const { user } = show(many, { inARow: true });

    await user.click(screen.getByRole("button", { name: /^Cindermoor Works/ }));

    expect(chips()).toHaveLength(8);
    expect(chips().map(wordsOf)).toContain(
      "Cindermoor Works, public transport assumed, 35 minutes, flexible assumed",
    );
    expect(screen.getByRole("group", { name: JOURNEY.place("Cindermoor Works") })).toBeInTheDocument();
    // While a chip is open the button that closes the row does nothing, and says so.
    expect(screen.getByRole("button", { name: CHIPS.showFewer })).toHaveAttribute("aria-disabled", "true");
  });

  test("test_with_few_chips_there_is_no_button_and_they_are_said_in_short_all_the_same", () => {
    show(meta.defaults.rent, { assumed: {}, readBy: null, inARow: true });

    expect(chips()).toHaveLength(1);
    expect(chips().map((chip) => chip.textContent)).toEqual([`Renting ${CHIPS.assumed}`]);
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

    await user.click(screen.getByRole("button", { name: /^Renting/ }));

    expect(canBeSeen(screen.getByText(CHIPS.assumedHint))).toBe(true);
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
    // Nor is what the part of the kit draws in it, whose words break where they must.
    expect(KIT.filter((rule) => rule.selector === ".label").map((rule) => rule.sets.get("max-width"))).toContain("100%");
    expect(KIT.filter((rule) => rule.selector === ".says").map((rule) => rule.sets.get("overflow-wrap"))).toContain("anywhere");
    // Text can be made larger: nothing of the row has a height it may not grow past.
    expect([...setBy("height"), ...setBy("max-height"), ...setBy("block-size"), ...setBy("max-block-size")]).toEqual([]);
  });

  test("test_turn_and_the_way_out_keep_their_width_so_that_each_is_whole_and_can_be_pressed", () => {
    // The words of a chip give way. What is pressed beside them does not. "Turn" is the
    // row's own, and the way out is the cross of the part of the kit.
    const turn = STYLES.filter((rule) => rule.under === null && isFor(rule.selector, "turn"));
    const cross = KIT.filter((rule) => rule.under === null && rule.selector === ".off");

    expect(new Set(turn.filter((rule) => rule.sets.has("flex")).map((rule) => subjectOf(rule.selector)))).toEqual(new Set([".turn"]));
    expect(turn.map((rule) => rule.sets.get("flex"))).toContain("none");
    expect(cross.map((rule) => rule.sets.get("flex"))).toEqual(["none"]);
  });

  test("test_turn_is_a_button_of_the_size_of_a_main_control_and_is_lit_in_hand_without_moving", () => {
    show(recordedAnswer("interpret", "interpret-scale").body.data.spec, { assumed: {} });

    for (const turn of screen.getAllByRole("button", { name: /^Turn / })) {
      expect(turn.tagName).toBe("BUTTON");
      expect(turn).toHaveClass("target");
    }
    const inHand = STYLES.filter((rule) => /:(hover|focus-visible|focus|active)\b/.test(rule.selector));
    expect(inHand.map((rule) => rule.selector).sort()).toEqual([".row:focus", ".turn:focus-visible", ".turn:hover"]);
    expect(inHand.filter((rule) => isFor(rule.selector, "turn")).flatMap((rule) => [...rule.sets.keys()])).toEqual([
      "background-color",
      "background-color",
    ]);
  });

  test("test_every_part_of_the_row_brings_the_ground_it_is_read_on_so_that_nothing_is_read_on_the_grass", () => {
    const groundOf = (part: string) =>
      STYLES.filter((rule) => rule.under === null && rule.selector === `.${part}`).flatMap((rule) => rule.sets.get("background") ?? []);

    // The plate and what explains the chips are page, with an edge of ink.
    for (const part of ["heading", "notes"]) {
      expect([part, groundOf(part)]).toEqual([part, ["var(--page)"]]);
      expect([part, STYLES.filter((rule) => rule.selector === `.${part}`).flatMap((rule) => rule.sets.get("border") ?? [])]).toEqual([
        part,
        ["var(--edge) solid var(--border)"],
      ]);
    }
    // The name of the plate is a short label: page on ink, in the face of names.
    const title = STYLES.filter((rule) => rule.under === null && rule.selector === ".title");
    expect(groundOf("title")).toEqual(["var(--ink)"]);
    expect(title.map((rule) => rule.sets.get("color"))).toEqual(["var(--page)"]);
    expect(title.map((rule) => rule.sets.get("font"))).toEqual(["400 var(--name-1) / 1 var(--font-name)"]);
    // A chip, the box its control stands in and the button that shows the rest are the
    // kit's, and each is drawn on page. The row itself lays no ground, and what holds a
    // sentence is never set in the face of names.
    expect(KIT.filter((rule) => rule.under === null && rule.selector === ".chip").map((rule) => rule.sets.get("background"))).toEqual([
      "var(--page)",
    ]);
    expect(groundOf("row")).toEqual([]);
    expect(STYLES.filter((rule) => /var\(--font-name\)/.test(rule.sets.get("font") ?? "")).map((rule) => rule.selector).sort()).toEqual([
      ".title",
      ".turn",
    ]);
  });

  test("test_every_word_of_the_row_is_ink_but_the_name_of_the_plate_which_is_page_on_ink", () => {
    // What nobody said was once drawn quieter. On sand, where a chip is in hand, and on
    // amber, where it is open, ink alone is read.
    const coloured = STYLES.filter((rule) => rule.sets.has("color") && !/forced-colors/.test(rule.under ?? ""));

    expect(coloured.map((rule) => [rule.selector, rule.sets.get("color")])).toEqual([
      [".heading", "var(--text)"],
      [".title", "var(--page)"],
      [".turn", "var(--ink)"],
      [".notes", "var(--text)"],
    ]);
  });
});

describe("the chips on a narrow row", () => {
  const STYLES = rulesOf(readFileSync(path.join(__dirname, "ChipRow.module.css"), "utf8"));
  const narrow = STYLES.filter((rule) => rule.under === "@container (max-width: 26rem)");
  const setOn = (selector: string) => new Map(narrow.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));
  /** How each chip lies: alone on its row, or beside another. */
  const lying = () => chips().map((chip) => chip.getAttribute("data-lies"));
  /** What the row hands the style sheet of a chip, by name. */
  const handed = (chip: HTMLElement | undefined, name: string) => chip?.style.getPropertyValue(name) ?? "";

  test("test_the_row_is_laid_out_by_its_own_width_and_not_by_that_of_the_screen", () => {
    expect(STYLES.filter((rule) => rule.selector === ".row").map((rule) => rule.sets.get("container-type"))).toEqual(["inline-size"]);
    expect(narrow.length).toBeGreaterThan(0);
    // No rule of the row asks how wide the screen is, but the one that asks how large a drawing is there.
    expect([...new Set(STYLES.map((rule) => rule.under).filter((under) => /\bwidth\b/.test(under ?? "")))]).toEqual([
      "@media (min-width: 60rem)",
      "@container (max-width: 26rem)",
    ]);
  });

  test("test_two_chips_that_say_little_share_a_row_and_every_other_has_the_row", () => {
    // Seen in a browser, on a phone: every chip on a row of its own, and the first result
    // below the first screen.
    show(first.spec, { inARow: true });

    expect(chips().map(wordsOf)).toHaveLength(5);
    // The two vibes, of which the second may set its words on two lines. The place and the
    // budget, which say much. Renting, which nothing follows.
    expect(lying()).toEqual(["keeps", "gives", "alone", "alone", "alone"]);
    // A chip has the row unless the row says that it shares it.
    expect(setOn(".chip").get("flex")).toBe("1 1 100%");
    // Each fills what it is given, so that the chips stand as one block.
    expect(setOn(".head").get("justify-self")).toBe("stretch");
  });

  test("test_a_chip_that_shares_a_row_is_never_made_narrower_than_its_words_so_that_no_word_is_broken", () => {
    // Seen in a browser: two chips were given a half of the row each, whatever they said,
    // and the name of an area was broken in the middle of a word to fit its half.
    const shrinks = (selector: string) => (setOn(selector).get("flex") ?? "").split(" ")[1];

    expect(setOn('.chip[data-lies="fills"]').get("flex")).toBe("1 0 auto");
    expect(setOn('.chip[data-lies="keeps"]').get("flex")).toBe("0 0 auto");
    for (const lies of ["fills", "keeps", "gives"]) expect([lies, shrinks(`.chip[data-lies="${lies}"]`)]).toEqual([lies, "0"]);
    // One that gives way is no narrower than its buttons and its words on two lines, which
    // the row counts and hands it. It takes what is left over, and its neighbour none of it.
    expect(setOn('.chip[data-lies="gives"]').get("flex")).toBe(
      "1 0 calc(var(--px) * 30 + var(--beside) * (var(--press) + var(--px)) + var(--letters) * 0.52 * var(--size-small))",
    );
    show(first.spec, { inARow: true });
    const [, quiet, place] = chips();
    expect([handed(quiet, "--beside"), handed(quiet, "--letters")]).toEqual(["1", "7"]);
    // A chip that does not give way is handed nothing.
    expect(place?.getAttribute("style")).toBeNull();
    // No rule of the narrow row lays the chips in columns, which every row would share.
    expect(narrow.filter((rule) => [...rule.sets.keys()].some((property) => /^grid/.test(property))).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_a_chip_that_is_open_has_the_row_and_so_has_the_one_that_stood_beside_it", async () => {
    const { user } = show(first.spec, { inARow: true });

    expect(lying().slice(0, 2)).toEqual(["keeps", "gives"]);
    await user.click(screen.getByRole("button", { name: /^Leafy/ }));

    const open = chips().findIndex((chip) => chip.getAttribute("data-open") === "true");
    expect(open).toBe(0);
    expect(lying().slice(0, 2)).toEqual(["alone", "alone"]);
  });

  test("test_no_chip_is_cut_there_and_none_is_hidden", () => {
    const hiding = narrow.filter((rule) =>
      [...rule.sets].some(([property, value]) => /^(overflow|display|visibility|white-space|text-overflow)/.test(property) && /hidden|none|nowrap|clip|ellipsis/.test(value)),
    );

    expect(hiding.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_the_words_of_a_chip_are_the_size_of_a_small_sentence_there_and_never_smaller", () => {
    expect(setOn(".head").get("--size-body")).toBe("var(--size-small)");
    // Everywhere else they are the size of a sentence. No size of the row is a figure of its
    // own, so that each grows with the size a person has set for text.
    const sizes = STYLES.filter((rule) => rule.sets.has("font-size")).map((rule) => [rule.selector, rule.sets.get("font-size")]);
    expect(sizes).toEqual([
      [".heading", "var(--size-small)"],
      [".head", "var(--size-body)"],
      [".notes", "var(--size-small)"],
    ]);
    // The control a chip opens is set as every control is: what makes the words of a chip
    // small is said of the chip itself, and of nothing that holds its control too.
    const small = STYLES.filter((rule) => rule.sets.has("--size-body") || rule.sets.has("font-size")).map((rule) => rule.selector);
    expect(small.filter((selector) => /\.chip|\.editor|\.line|\.row/.test(selector))).toEqual([]);
  });

  test("test_a_chip_of_two_lines_is_no_higher_than_a_chip_of_one_so_that_the_first_result_stays_on_the_first_screen", () => {
    // Measured in a browser 390 wide, on a plain search: with its two lines set as far
    // apart as a sentence's, a chip was 60 px high and the first result ended 31 px under
    // the first screen. Set as close as the reading face sets its own lines, and from the
    // top of their block, two lines are 36 px: with the room a chip keeps round its words
    // that is 44, the height of a main control, which a chip of one line has already.
    const words = new Map(STYLES.filter((rule) => rule.selector === ".words").flatMap((rule) => [...rule.sets]));

    expect([...words]).toEqual([
      ["display", "inline-block"],
      ["line-height", "1.2"],
      ["vertical-align", "top"],
    ]);
    // One row stands on the next: the room of a shadow is all that parts them.
    expect(setOn(".line").get("gap")).toBe("0 var(--space-1)");
  });

  test("test_a_chip_of_a_narrow_row_is_as_high_as_two_lines_of_its_words_and_its_edge_and_no_higher", () => {
    // Measured in a browser 390 wide, with every part of the page dressed: a chip was 48 px
    // with its edge and four rows of them 208, and the first result ended 150 px under the
    // foot of the first screen. What stands over the answer gives way, and after the room
    // between two boxes the height of a chip is the next to. Two lines of its words are 36
    // px, and with its edge that is 40: what is pressed in it is 36 px high and wide, which
    // is lower than a main control, and half as high again as a small one.
    // It is said of each part of the row, so that the line of the heading reads it as the chips do.
    expect(setOn(".row > *").get("--press")).toBe("calc(var(--target) - var(--px) * 4)");
    expect(setOn(".line").get("--press")).toBeUndefined();
    expect([setOn(".head").get("--target"), setOn(".head").get("--label-room")]).toEqual(["var(--press)", "0px"]);
    const tokens = asWritten();
    const press = Number.parseInt(tokens["--target"] ?? "", 10) - Number.parseInt(tokens["--px"] ?? "", 10) * 4;
    expect(press).toBe(36);
    expect(press).toBeGreaterThanOrEqual(Number.parseInt(tokens["--target-min"] ?? "", 10) * 1.5);
    // Two lines of its words, set as close as the row sets them, are as high as what is pressed.
    expect(2 * 1.2 * Number.parseFloat(tokens["--size-small"] ?? "") * 16).toBe(press);
    // It is said of the chip itself and of the line that opens the rest of them, and never
    // of the control a chip opens, which is set as every control is.
    expect(narrow.filter((rule) => rule.sets.has("--target") || rule.sets.has("--label-room")).map((rule) => rule.selector)).toEqual([".rest", ".head"]);
    expect(STYLES.filter((rule) => rule.under !== "@container (max-width: 26rem)" && (rule.sets.has("--target") || rule.sets.has("--press"))).map((rule) => rule.selector)).toEqual([]);
    // Before it has any chip the line is as high as one, with the room of its shadow.
    expect([setOn(".line").get("min-height"), setOn(".holding").get("min-height")]).toEqual(["var(--target)", "var(--target)"]);
  });
});

describe("the button that opens the rest of the chips", () => {
  const STYLES = rulesOf(readFileSync(path.join(__dirname, "ChipRow.module.css"), "utf8"));
  const follows = (one: Element, other: Element) =>
    Boolean(one.compareDocumentPosition(other) & Node.DOCUMENT_POSITION_FOLLOWING);

  test("test_it_stands_on_the_line_of_the_heading_over_the_chips_so_that_it_is_where_it_was_once_they_are_opened_out", async () => {
    // Measured on a phone: it stood after the chips, and went 132 px down the window under
    // the press that opened them out. Nothing that opens stands over it now.
    const { user } = show(many, { inARow: true });
    const rest = screen.getByRole("button", { name: CHIPS.rest(2) });
    const list = screen.getByRole("list");

    expect(follows(heading(), rest)).toBe(true);
    expect(follows(rest, list)).toBe(true);
    expect(rest.parentElement).toBe(heading().closest("p")?.parentElement);
    // It says which list it opens out.
    expect(rest).toHaveAttribute("aria-controls", list.id);

    await user.click(rest);

    expect(follows(rest, screen.getByRole("list"))).toBe(true);
    // What explains the chips stands under them, as it did.
    expect(follows(screen.getByRole("list"), screen.getByText(CHIPS.assumedHint))).toBe(true);
  });

  test("test_it_is_of_one_size_whichever_it_says_for_it_holds_the_room_of_both", async () => {
    // "+3 more" became "Show fewer" under the press, which is wider by four letters.
    const { user } = show(many, { inARow: true });
    const rest = screen.getByRole("button", { name: CHIPS.rest(2) });
    const said = () => [...rest.querySelectorAll<HTMLElement>("[data-said]")];
    const heard = () => said().filter((one) => one.closest("[aria-hidden='true']") === null).map((one) => one.textContent);

    expect(said().map((one) => one.textContent)).toEqual([CHIPS.rest(2), CHIPS.showFewer]);
    expect(said().map((one) => one.getAttribute("data-said"))).toEqual(["true", "false"]);
    expect(heard()).toEqual([CHIPS.rest(2)]);

    await user.click(rest);

    expect(said().map((one) => one.getAttribute("data-said"))).toEqual(["false", "true"]);
    expect(heard()).toEqual([CHIPS.showFewer]);
    // Both stand in one place, and the one that is not said keeps its room and is not drawn.
    const both = STYLES.filter((rule) => rule.under === null && isFor(rule.selector, "said"));
    expect(both.map((rule) => [rule.selector, [...rule.sets]])).toEqual([
      [".said", [["grid-area", "1 / 1"]]],
      ['.said[data-said="false"]', [["visibility", "hidden"]]],
    ]);
    expect(STYLES.filter((rule) => rule.selector === ".says").map((rule) => rule.sets.get("display"))).toEqual(["inline-grid"]);
  });

  test("test_the_heading_and_the_button_share_a_line_that_is_never_wider_than_the_row", () => {
    const top = STYLES.filter((rule) => rule.under === null && rule.selector === ".top");

    expect(top.map((rule) => [rule.sets.get("display"), rule.sets.get("justify-content"), rule.sets.get("min-width")])).toEqual([
      ["flex", "space-between", "0"],
    ]);
    // Where both do not fit on one line the button takes the next, whole.
    expect(top[0]?.sets.get("flex-wrap")).toBe("wrap");
  });
});

describe("a search of many things on a narrow row", () => {
  /**
   * Says how wide the row is, as a browser that lays it out would. jsdom lays nothing out
   * and measures nothing, so every other test of the row is of a wide one.
   */
  const asWideAs = (width: number) =>
    jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function measured(this: HTMLElement) {
      const wide = this.tagName === "SECTION" ? width : 0;
      return { width: wide, height: 0, top: 0, left: 0, right: wide, bottom: 0, x: 0, y: 0, toJSON: () => ({}) };
    });
  /** A phone 390 wide: the row stands in the search box, which holds 338 px. */
  const PHONE = 338;

  test("test_it_folds_to_two_rows_and_a_line_that_opens_the_rest_and_says_how_many_it_holds", async () => {
    // Measured on a phone 390 wide, on a search of seven things: seven chips in six rows,
    // and the first result from 590 to 1,118 of 844, where a plain search leaves it whole.
    asWideAs(PHONE);
    const { user } = show(many, { inARow: true });

    // Two that say little share the first row, and the third has the second.
    expect(chips().map(wordsOf)).toEqual(["Leafy", "Quiet streets", "Village feel"]);
    expect(chips().map((chip) => chip.getAttribute("data-lies"))).toEqual(["keeps", "gives", "alone"]);
    // The search holds eight: five wait, and the line says so.
    const rest = screen.getByRole("button", { name: CHIPS.rest(5) });
    expect(rest).toHaveAttribute("aria-expanded", "false");
    expect(screen.getAllByRole("button", { name: /more$/ })).toHaveLength(1);

    await user.click(rest);

    // What was folded is one press away, and nothing of it is lost or cut.
    expect(chips()).toHaveLength(8);
    expect(chips().map(wordsOf).at(-1)).toBe("Renting");
    expect(screen.getByRole("button", { name: CHIPS.showFewer })).toHaveFocus();
    await user.click(screen.getByRole("button", { name: CHIPS.showFewer }));
    expect(chips()).toHaveLength(3);
    expect(screen.getByRole("button", { name: CHIPS.rest(5) })).toHaveFocus();
  });

  test("test_the_button_that_opens_the_rest_is_as_high_as_what_is_pressed_in_a_chip_there", () => {
    // Measured on a phone 390 wide with the button on a line of its own under the chips, as
    // high as a main control and the room of a shadow under it: two rows and the line were
    // 162 px, and a first result 442 px high ended 12 px under the first screen. It is as
    // high as what is pressed in a chip, and stands on the line of the heading.
    const STYLES = rulesOf(readFileSync(path.join(__dirname, "ChipRow.module.css"), "utf8"));
    const narrow = STYLES.filter((rule) => rule.under === "@container (max-width: 26rem)");
    const line = new Map(narrow.filter((rule) => rule.selector === ".rest").flatMap((rule) => [...rule.sets]));

    expect([...line]).toEqual([["--target", "var(--press)"]]);
    // How high that is, is said where the button can read it as the chips do.
    const press = narrow.filter((rule) => rule.sets.has("--press")).map((rule) => rule.selector);
    expect(press).toEqual([".row > *"]);
    // It is drawn by the button of the kit, which is as high as a target is wherever it stands.
    asWideAs(PHONE);
    show(many, { inARow: true });
    expect(screen.getByRole("button", { name: CHIPS.rest(5) })).toHaveClass("press", "target", "rest");
  });

  test("test_a_chip_that_is_pressed_opens_the_row_out_as_it_does_on_any_row", async () => {
    asWideAs(PHONE);
    const { user } = show(many, { inARow: true });

    await user.click(screen.getByRole("button", { name: /^Quiet streets/ }));

    expect(chips()).toHaveLength(8);
    expect(chips().find((chip) => chip.getAttribute("data-open") === "true")).toHaveTextContent(/^Quiet streets/);
  });

  test("test_a_search_whose_chips_stand_in_three_rows_is_all_in_sight_and_one_of_four_folds", () => {
    // Measured on a phone 390 wide on 2026-09-27: the five chips of a plain search stood in
    // four rows, every one in sight, and its first result ended 9 px under the first
    // screen, from 470 to 853 of 844.
    asWideAs(PHONE);
    // The same search with no journey: its two vibes share a row, and its budget and its
    // tenure have one each.
    const three = show({ ...first.spec, commutes: [] }, { inARow: true });

    expect(chips().map((chip) => chip.getAttribute("data-lies"))).toEqual(["keeps", "gives", "alone", "alone"]);
    expect(screen.queryByRole("button", { name: /more$/ })).toBeNull();
    three.unmount();

    show(first.spec, { inARow: true });

    expect(chips().map((chip) => chip.getAttribute("data-lies"))).toEqual(["keeps", "gives", "alone"]);
    expect(screen.getByRole("button", { name: CHIPS.rest(2) })).toHaveAttribute("aria-expanded", "false");
  });

  test("test_a_plain_search_stands_over_the_answer_as_it_was_measured_by_what_each_chip_says_and_the_lines_that_takes", async () => {
    // Measured on a phone 390 wide on 2026-09-27, after "Renting a 1 bed for about £1,700 a
    // month, leafy and quiet, 35 minutes to Cindermoor Works". A chip whose words take one
    // line or two is 44 px high with what parts it from the next, and each line more is
    // 18 px more: the chip of the journey came to say every part of itself, which is three
    // lines and 62 px, and nothing measured the first result with it. So what the chips
    // of this search say is held here, with the lines that takes. Where this fails, a chip
    // says something else than was measured: measure the first result in a browser again,
    // at 390 by 844, before what is held here is brought to what the chip now says.
    asWideAs(PHONE);
    const { user } = show(first.spec, { inARow: true });
    /**
     * How many lines the words of a chip take where it has a narrow row to itself, by the
     * count of letters the row is laid out by: what a row holds from edge to edge, less
     * what the chip takes beside its words. No word is broken.
     */
    const linesOf = (chip: HTMLElement) => {
      const words = wordsOf(chip);
      const beside = chip.querySelectorAll("button:not([data-main])").length;
      const line = NARROW_ROW - (roomOf({ words, cross: beside > 0, turn: beside > 1 }) - words.length);
      return words.split(" ").reduce(
        (set, word) => (set.held > 0 && set.held + 1 + word.length > line ? { lines: set.lines + 1, held: word.length } : { lines: set.lines, held: set.held === 0 ? word.length : set.held + 1 + word.length }),
        { lines: 1, held: 0 },
      ).lines;
    };

    // Two rows stand over the answer: the two vibes in one, and the journey in the next.
    expect(chips().map(wordsOf)).toEqual([
      "Leafy",
      "Quiet streets",
      "Cindermoor Works, public transport assumed, 35 minutes, flexible assumed",
    ]);
    expect(chips().map((chip) => chip.getAttribute("data-lies"))).toEqual(["keeps", "gives", "alone"]);
    expect(linesOf(chips()[2] as HTMLElement)).toBe(3);
    // The button says how many it holds, and is the one button of the row that does.
    const rest = screen.getByRole("button", { name: CHIPS.rest(2) });
    expect(screen.getAllByRole("button", { name: /more$/ })).toEqual([rest]);

    await user.click(rest);

    // What was folded is one press away, and says what it said: the budget on two lines.
    expect(chips().map(wordsOf).slice(3)).toEqual(["£1,700 a month, one bedroom, flexible assumed", "Renting"]);
    expect(chips().slice(2).map(linesOf)).toEqual([3, 2, 1]);
    expect(rest).toHaveFocus();
    expect(rest).toHaveAccessibleName(CHIPS.showFewer);

    await user.click(rest);

    expect(chips()).toHaveLength(3);
    expect(rest).toHaveFocus();
    expect(rest).toHaveAccessibleName(CHIPS.rest(2));
  });

  test("test_it_is_narrow_by_its_own_width_and_a_row_that_is_wider_holds_six_as_it_did", () => {
    // The width the style sheet lays a narrow row out by, 26rem, and one pixel more.
    asWideAs(26 * 16 + 1);
    const wide = show(many, { inARow: true });
    expect(chips()).toHaveLength(SHOWN_AT_FIRST);
    expect(screen.getByRole("button", { name: CHIPS.rest(2) })).toBeInTheDocument();
    wide.unmount();

    asWideAs(26 * 16);
    show(many, { inARow: true });
    expect(chips()).toHaveLength(3);
  });

  test("test_a_browser_that_lays_nothing_out_is_taken_for_a_wide_one", () => {
    show(many, { inARow: true });

    expect(chips()).toHaveLength(SHOWN_AT_FIRST);
  });

  test("test_nothing_of_the_fold_is_the_style_sheets_so_that_what_is_in_sight_is_what_is_heard", () => {
    // What is folded is not drawn at all until it is asked for: it is kept from nobody by
    // a style, which a screen reader or a keyboard might not follow.
    const STYLES = rulesOf(readFileSync(path.join(__dirname, "ChipRow.module.css"), "utf8"));
    const hiding = STYLES.filter((rule) => /^\.(chip|chips|line|rest)\b/.test(rule.selector) && /none|hidden/.test(rule.sets.get("display") ?? rule.sets.get("visibility") ?? ""));

    expect(hiding.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_the_folded_row_has_no_accessibility_fault", async () => {
    asWideAs(PHONE);
    const { container } = show(many, { inARow: true });

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("a search of many things on a wide row", () => {
  // Burro takes what it noticed in a sentence of itself, so a sentence of a dozen things
  // is a search of a dozen chips. Measured at 1440 by 900 after the founder's own sentence:
  // six chips stood in five rows of 280 px, and the first result began at 909 of 900, out
  // of sight. A plain search is five chips in three rows, and its first result begins at 687.
  /** A desk 1440 wide: the row stands in the search box, which holds 590 px. */
  const DESK = 590;
  /** How high a row of chips is there, with what parts it from the next. */
  const ROW = 56;
  /**
   * Lays the chips out as a browser would: the row is as wide as a desk's, and each chip
   * stands in the row it is given, in the order they are drawn in. A chip that is given
   * none stands in the last. jsdom lays nothing out, so every chip stands at nought there.
   */
  function laidIn(rows: readonly number[]) {
    jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function measured(this: HTMLElement) {
      const wide = this.tagName === "SECTION" ? DESK : 0;
      return { width: wide, height: 0, top: 0, left: 0, right: wide, bottom: 0, x: 0, y: 0, toJSON: () => ({}) };
    });
    jest.spyOn(HTMLElement.prototype, "offsetTop", "get").mockImplementation(function stands(this: HTMLElement) {
      if (this.tagName !== "LI" || this.parentElement === null) return 0;
      const at = [...this.parentElement.children].indexOf(this);
      return ((rows[at] ?? rows.at(-1) ?? 1) - 1) * ROW;
    });
  }

  test("test_it_folds_to_two_rows_and_a_line_that_opens_the_rest_and_says_how_many_it_holds", async () => {
    // Six chips in five rows: one, two, and then one to a row.
    laidIn([1, 2, 2, 3, 4, 5]);
    const { user } = show(many, { inARow: true });

    expect(WIDE_ROWS).toEqual({ most: 3, folded: 2 });
    expect(chips().map(wordsOf)).toEqual(["Leafy", "Quiet streets", "Village feel"]);
    // The search holds eight: five wait, and the line says so.
    const rest = screen.getByRole("button", { name: CHIPS.rest(5) });
    expect(rest).toHaveAttribute("aria-expanded", "false");
    expect(screen.getAllByRole("button", { name: /more$/ })).toHaveLength(1);

    await user.click(rest);

    // What was folded is one press away, and nothing of it is lost or cut.
    expect(chips()).toHaveLength(8);
    expect(chips().map(wordsOf).at(-1)).toBe("Renting");
    expect(screen.getByRole("button", { name: CHIPS.showFewer })).toHaveFocus();
    await user.click(screen.getByRole("button", { name: CHIPS.showFewer }));
    expect(chips()).toHaveLength(3);
    expect(screen.getByRole("button", { name: CHIPS.rest(5) })).toHaveFocus();
  });

  test("test_the_button_that_opens_the_rest_folds_them_again_though_the_search_holds_no_more_than_six", async () => {
    // Seen at 1440 by 900, of a search of five chips that stood in more rows than three:
    // "+3 more" went as it was pressed, left the focus on nothing, and left nothing that
    // folded the chips again. On a phone the same button became "Show fewer", and kept
    // the focus. They are one button.
    laidIn([1, 2, 3, 4, 5]);
    const { user } = show(first.spec, { inARow: true });
    expect(chips()).toHaveLength(2);
    const rest = screen.getByRole("button", { name: CHIPS.rest(3) });

    await user.click(rest);

    expect(chips()).toHaveLength(5);
    expect(rest).toBeInTheDocument();
    expect(rest).toHaveFocus();
    expect(rest).toHaveAccessibleName(CHIPS.showFewer);
    expect(rest).toHaveAttribute("aria-expanded", "true");

    await user.click(rest);

    expect(chips()).toHaveLength(2);
    expect(rest).toHaveFocus();
    expect(rest).toHaveAccessibleName(CHIPS.rest(3));
    expect(rest).toHaveAttribute("aria-expanded", "false");
  });

  test("test_where_nothing_is_left_to_fold_as_the_row_is_folded_again_the_button_goes_and_hands_the_focus_to_the_row", async () => {
    laidIn([1, 2, 3, 4, 5]);
    const view = show(first.spec, { inARow: true });
    await view.user.click(screen.getByRole("button", { name: CHIPS.rest(3) }));
    // The place and the budget are taken off while the row stands opened out: folded, what
    // is left stands in two rows.
    jest.restoreAllMocks();
    laidIn([1, 1, 2]);
    const fewer: PreferenceSpec = { ...first.spec, commutes: [], budget: { ...first.spec.budget, amount: null } };
    view.rerender(
      <ChipRow
        spec={fewer}
        assumed={{}}
        placeNames={{}}
        meta={meta}
        areas={areas}
        onEdit={() => undefined}
        onTenure={() => undefined}
        version={2}
        readBy="rule"
      />,
    );
    expect(chips()).toHaveLength(3);
    // What opened the row out folds it again, whatever it holds by then.
    const rest = screen.getByRole("button", { name: CHIPS.showFewer });

    await view.user.click(rest);

    expect(chips()).toHaveLength(3);
    expect(screen.queryByRole("button", { name: /more$|fewer$/ })).toBeNull();
    // The focus is never left on nothing.
    expect(screen.getByRole("region", { name: CHIPS.label })).toHaveFocus();
  });

  test("test_the_button_is_the_button_it_was_with_the_focus_it_had_where_the_row_is_read_again_as_it_folds", async () => {
    laidIn([1, 2, 3, 4, 5]);
    const view = show(first.spec, { inARow: true });
    await view.user.click(screen.getByRole("button", { name: CHIPS.rest(3) }));
    // The budget is taken off while the row stands opened out: folded, what is left stands in four rows.
    jest.restoreAllMocks();
    laidIn([1, 2, 3, 4]);
    const fewer: PreferenceSpec = { ...first.spec, budget: { ...first.spec.budget, amount: null } };
    view.rerender(
      <ChipRow
        spec={fewer}
        assumed={ASSUMED}
        placeNames={PLACES}
        meta={meta}
        areas={areas}
        onEdit={() => undefined}
        onTenure={() => undefined}
        version={2}
        readBy="rule"
      />,
    );
    const rest = screen.getByRole("button", { name: CHIPS.showFewer });

    await view.user.click(rest);

    expect(chips()).toHaveLength(2);
    expect(rest).toBeInTheDocument();
    expect(rest).toHaveFocus();
    expect(rest).toHaveAccessibleName(CHIPS.rest(2));
  });

  test("test_a_search_whose_chips_stand_in_three_rows_is_all_in_sight_as_it_was", () => {
    // Measured at 1440 by 900: the five chips of a plain search stand in three rows.
    laidIn([1, 1, 2, 3, 3]);
    show(first.spec, { inARow: true });

    expect(chips()).toHaveLength(5);
    expect(screen.queryByRole("button", { name: /more$/ })).toBeNull();
  });

  test("test_six_chips_that_stand_in_three_rows_are_the_six_the_row_holds_at_first", () => {
    laidIn([1, 1, 2, 2, 3, 3]);
    show(many, { inARow: true });

    expect(chips()).toHaveLength(SHOWN_AT_FIRST);
    expect(screen.getByRole("button", { name: CHIPS.rest(2) })).toBeInTheDocument();
  });

  test("test_a_chip_that_is_pressed_opens_the_row_out_as_it_does_on_any_row", async () => {
    laidIn([1, 2, 2, 3, 4, 5]);
    const { user } = show(many, { inARow: true });

    await user.click(screen.getByRole("button", { name: /^Quiet streets/ }));

    expect(chips()).toHaveLength(8);
    expect(chips().find((chip) => chip.getAttribute("data-open") === "true")).toHaveTextContent(/^Quiet streets/);
  });

  test("test_a_search_that_comes_to_hold_more_is_measured_again_and_one_that_holds_less_is_drawn_whole", () => {
    laidIn([1, 2, 2, 3, 4, 5]);
    const view = show(many, { inARow: true });
    expect(chips()).toHaveLength(3);

    // Two vibes are taken off: what is left stands in three rows, and is drawn whole.
    jest.restoreAllMocks();
    laidIn([1, 1, 2, 3, 3, 3]);
    const fewer = { ...many, tags: many.tags.slice(0, 3) };
    view.rerender(
      <ChipRow
        spec={fewer}
        assumed={{}}
        placeNames={{}}
        meta={meta}
        areas={areas}
        onEdit={() => undefined}
        onTenure={() => undefined}
        version={2}
      />,
    );

    expect(chips()).toHaveLength(6);
    expect(screen.queryByRole("button", { name: /more$/ })).toBeNull();
  });

  test("test_nothing_is_folded_on_a_narrow_row_by_where_a_chip_stands_for_it_folds_by_its_own_count", () => {
    // A phone folds by what its chips say, before anything is drawn: measured there, the
    // first rows of a search would be drawn and taken away again under the eye.
    jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function measured(this: HTMLElement) {
      const wide = this.tagName === "SECTION" ? 338 : 0;
      return { width: wide, height: 0, top: 0, left: 0, right: wide, bottom: 0, x: 0, y: 0, toJSON: () => ({}) };
    });
    jest.spyOn(HTMLElement.prototype, "offsetTop", "get").mockImplementation(() => 0);
    show(many, { inARow: true });

    expect(chips().map(wordsOf)).toEqual(["Leafy", "Quiet streets", "Village feel"]);
    expect(chips().map((chip) => chip.getAttribute("data-lies"))).toEqual(["keeps", "gives", "alone"]);
  });

  test("test_the_folded_row_has_no_accessibility_fault", async () => {
    laidIn([1, 2, 2, 3, 4, 5]);
    const { container } = show(many, { inARow: true });

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("how large a chip is drawn on a wide screen", () => {
  const STYLES = rulesOf(readFileSync(path.join(__dirname, "ChipRow.module.css"), "utf8"));
  const WIDE = "@media (min-width: 60rem)";
  const NARROW = "@container (max-width: 26rem)";

  test("test_one_line_chooses_and_the_row_says_which", () => {
    show();

    expect(["screen", "small"]).toContain(ON_A_WIDE_SCREEN);
    expect(screen.getByRole("region", { name: CHIPS.label })).toHaveAttribute("data-art", ON_A_WIDE_SCREEN);
  });

  test("test_a_chip_is_drawn_small_there_so_that_the_first_result_is_in_sight_and_what_is_pressed_in_it_is_a_main_control_still", () => {
    // Measured at 1440 by 900 after a plain search, beside the map as wide as it now is: at
    // three pixels of the screen to one of a drawing a chip was 66 px high with its edge,
    // the five chips of the search stood in four rows of 300 px, and the first result
    // began at 899 of 900. At two a chip is 48 px with its edge, the five stand in three
    // rows of 164 px, and the first result begins 136 px higher.
    show(first.spec, { inARow: true });

    expect(ON_A_WIDE_SCREEN).toBe("small");
    expect(screen.getByRole("region", { name: CHIPS.label })).toHaveAttribute("data-art", "small");
    // What gives way is the size of the drawing and of the edge, which is the art pixel. What
    // is pressed in a chip is as high as a main control is on every row but a narrow one.
    const wide = STYLES.filter((rule) => rule.under === WIDE);
    expect(wide.flatMap((rule) => [...rule.sets.keys()])).toEqual(["--px"]);
    expect(STYLES.filter((rule) => rule.under !== NARROW && [...rule.sets.keys()].some((set) => /^(--target|--press|min-height|height)$/.test(set))).map((rule) => [rule.selector, [...rule.sets.keys()].filter((set) => /height/.test(set))])).toEqual([
      [".line", ["min-height"]],
      [".holding", ["min-height"]],
      [".held", ["min-height"]],
    ]);
    const kit = rulesOf(readFileSync(path.join(__dirname, "..", "kit", "Label", "Label.module.css"), "utf8"));
    expect(kit.filter((rule) => rule.under === null && rule.selector === ".chip").map((rule) => rule.sets.get("min-height"))).toEqual(["var(--target)"]);
    expect(Number.parseInt(asWritten()["--target"] ?? "", 10)).toBe(44);
  });

  test("test_two_chips_stand_in_one_row_there_wherever_two_fit_and_none_is_given_the_row_but_one_that_is_open", () => {
    // Seen at 1440 by 900: drawn small, the two vibes of a plain search share the first
    // row and its budget and its tenure the third. The chips wrap as they fall, and the
    // row gives a chip the whole of a line only while the control it opens stands under it.
    const line = new Map(STYLES.filter((rule) => rule.under === null && rule.selector === ".line").flatMap((rule) => [...rule.sets]));

    expect([line.get("display"), line.get("flex-wrap")]).toEqual(["flex", "wrap"]);
    const takesTheRow = STYLES.filter((rule) => rule.under !== NARROW && /\.chip\b/.test(rule.selector) && [...rule.sets].some(([set, to]) => /^flex(-basis)?$/.test(set) && /100%/.test(to)));
    expect(takesTheRow.map((rule) => rule.selector)).toEqual(['.chip[data-open="true"]']);
    // No chip of a wide row is made as wide as the row, or is stretched to fill it.
    const chip = new Map(STYLES.filter((rule) => rule.under === null && rule.selector === ".chip").flatMap((rule) => [...rule.sets]));
    expect([chip.get("max-width"), chip.has("width"), chip.has("flex")]).toEqual(["100%", false, false]);
  });

  test("test_the_page_may_ask_for_the_chips_small_where_what_stands_over_the_answer_must_give_way", () => {
    // Measured at 1440 by 900 where Burro asks which place was meant: three chips stood in
    // two rows, 178 px, over a first result that began under the foot of the window. Drawn
    // small they stand in one row. The height of a chip gives way to the answer.
    show(first.spec, { art: "small" });

    expect(screen.getByRole("region", { name: CHIPS.label })).toHaveAttribute("data-art", "small");
  });

  test("test_drawn_small_a_chip_has_the_art_pixel_of_a_phone_and_the_control_it_opens_has_the_screens", () => {
    const small = STYLES.filter((rule) => /data-art/.test(rule.selector));

    expect(small.map((rule) => [rule.under, rule.selector, [...rule.sets]])).toEqual([
      ["@media (min-width: 60rem)", '.row[data-art="small"] .head', [["--px", "var(--px-small)"]]],
    ]);
    // It is the pixel of a phone by its own name, and not the pixel of the ground, which is the meadow's.
    expect(asWritten()["--px-small"]).toBe("2px");
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
    expect(document.querySelector("[data-turns]")).toBeNull();
  });

  test("test_a_chip_of_a_scale_keeps_the_room_of_what_it_says_once_it_is_turned_so_that_turn_stands_where_it_was_pressed", () => {
    // Measured at 1440 by 900: "Turn" went 9 px along the row under the press, as the chip
    // came to name the other end of its scale, whose name is shorter.
    const sheet = rulesOf(readFileSync(path.join(__dirname, "ChipRow.module.css"), "utf8")).filter((rule) => rule.under === null);
    const setsOf = (selector: string) => new Map(sheet.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));
    show(calm.spec, { assumed: { "tag:pace": ["weight"] } });

    const main = screen.getByRole("button", { name: new RegExp(`^${CHIPS.towards("Going out", "Calm")}`) });
    const words = main.querySelector("[data-turns]") as HTMLElement;
    const [now, then] = [...words.children] as HTMLElement[];
    // What it says now is what is read and heard, and all that is.
    expect(now?.textContent).toBe(`${CHIPS.towards("Going out", "Calm")} ${CHIPS.assumed}`);
    expect(main.textContent).toBe(now?.textContent);
    // What it says once it is turned lies in the same place, laid out and not drawn, in the
    // faces it is set in: it is in no text of the page, and is kept from whoever hears it.
    expect(then).toHaveAttribute("aria-hidden", "true");
    expect(then?.textContent).toBe("");
    expect([...(then?.querySelectorAll("[data-says]") ?? [])].map((part) => [part.className, part.getAttribute("data-says")])).toEqual([
      ["label", CHIPS.towards("Going out", "Buzzy")],
      ["assumed", ` ${CHIPS.assumed}`],
    ]);
    expect(setsOf(".words[data-turns]").get("display")).toBe("inline-grid");
    expect(setsOf(".words[data-turns] > *").get("grid-area")).toBe("1 / 1");
    expect(setsOf(".then").get("visibility")).toBe("hidden");
    expect(setsOf(".then [data-says]::before").get("content")).toBe("attr(data-says)");
  });

  test("test_a_chip_that_is_turned_is_no_narrower_than_it_was_as_it_was_pressed", async () => {
    // What nobody said of a vibe is said no longer once a person turns it: the chip said
    // less, and "Turn" went back along the row by as much as the word "assumed" is wide.
    const measure = jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (this: HTMLElement) {
      const wide = this.hasAttribute("data-turns") ? 236.5 : this.tagName === "SECTION" ? 600 : 0;
      return { top: 0, bottom: 0, left: 0, right: wide, x: 0, y: 0, width: wide, height: 0, toJSON: () => ({}) };
    });
    try {
      const { user, rerender } = show(calm.spec, { assumed: { "tag:pace": ["weight"] } });
      const words = () => document.querySelector("[data-turns]") as HTMLElement;
      expect(words().style.minWidth).toBe("");

      await user.click(screen.getByRole("button", { name: CHIPS.turnTo("Going out", "Buzzy") }));
      rerender(
        <ChipRow
          spec={turned.body.data.spec}
          assumed={{}}
          placeNames={PLACES}
          meta={meta}
          areas={areas}
          onEdit={() => undefined}
          onTenure={() => undefined}
          version={2}
          readBy="rule"
        />,
      );

      expect(words().textContent).toBe(CHIPS.towards("Going out", "Buzzy"));
      expect(words().style.minWidth).toBe("236.5px");
    } finally {
      measure.mockRestore();
    }
  });

  test("test_on_a_narrow_row_a_chip_that_is_turned_keeps_no_room_of_its_own_since_it_is_laid_out_by_the_row", async () => {
    const measure = jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (this: HTMLElement) {
      const wide = this.hasAttribute("data-turns") ? 236.5 : this.tagName === "SECTION" ? 358 : 0;
      return { top: 0, bottom: 0, left: 0, right: wide, x: 0, y: 0, width: wide, height: 0, toJSON: () => ({}) };
    });
    try {
      const { user } = show(calm.spec, { assumed: {} });

      await user.click(screen.getByRole("button", { name: CHIPS.turnTo("Going out", "Buzzy") }));

      expect((document.querySelector("[data-turns]") as HTMLElement).style.minWidth).toBe("");
    } finally {
      measure.mockRestore();
    }
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
