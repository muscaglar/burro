/**
 * The two ways into a search, as tabs. What is held here is what a tab is to a keyboard
 * and to a screen reader, and what the style sheet says of how one is drawn. jsdom lays
 * nothing out: that the chosen tab joins its panel was seen in a browser.
 */

import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf, weightOf } from "../../../test/support/css";
import { panelOf, Ways, type Way } from "./Ways";

const user = () => userEvent.setup({ delay: null });

type Id = "one" | "two" | "three";

const TWO: readonly Way<Id>[] = [
  { id: "one", label: "The first way" },
  { id: "two", label: "The second way" },
];
const THREE: readonly Way<Id>[] = [...TWO, { id: "three", label: "The third way" }];

/** The tabs as a page holds them: it keeps which is chosen, and draws a panel for each. */
function Held({ ways = TWO, heard }: { readonly ways?: readonly Way<Id>[]; readonly heard?: (id: Id) => void }) {
  const [chosen, setChosen] = useState<Id>("one");
  return (
    <main>
      <h1>A page</h1>
      <Ways
        label="Ways in"
        name="ways"
        ways={ways}
        chosen={chosen}
        onChoose={(id) => {
          heard?.(id);
          setChosen(id);
        }}
      />
      {ways.map((way) => (
        <div key={way.id} {...panelOf("ways", way.id, chosen)}>
          <button type="button">inside {way.label}</button>
        </div>
      ))}
    </main>
  );
}

const list = () => screen.getByRole("tablist", { name: "Ways in" });
const tab = (name: string) => within(list()).getByRole("tab", { name });
const tabs = () => within(list()).getAllByRole("tab");

const RULES = rulesOf(readFileSync(path.join(__dirname, "Ways.module.css"), "utf8"));
const ALWAYS = RULES.filter((rule) => rule.under === null);
const setBy = (selector: string) => new Map(ALWAYS.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));

describe("the two ways in, as tabs", () => {
  test("test_there_is_one_list_of_tabs_and_each_is_a_native_button_that_says_whether_it_is_chosen", () => {
    render(<Held />);

    expect(screen.getAllByRole("tablist")).toHaveLength(1);
    expect(tabs().map((one) => [one.textContent, one.getAttribute("aria-selected")])).toEqual([
      ["The first way", "true"],
      ["The second way", "false"],
    ]);
    for (const one of tabs()) {
      expect(one.tagName).toBe("BUTTON");
      expect(one).toHaveAttribute("type", "button");
      expect(one).toHaveClass("target");
      // It says that it is chosen, and never that it is pressed or open: it is a tab.
      expect(one).not.toHaveAttribute("aria-pressed");
      expect(one).not.toHaveAttribute("aria-expanded");
    }
    // Nothing but the tabs stands in the list, so that a screen reader counts them: one of two.
    expect([...list().children].map((part) => part.getAttribute("role"))).toEqual(["tab", "tab"]);
  });

  test("test_each_tab_names_the_panel_it_shows_and_each_panel_is_named_by_its_tab", () => {
    render(<Held />);

    for (const one of tabs()) {
      const panel = document.getElementById(one.getAttribute("aria-controls") ?? "");
      expect(panel).toHaveAttribute("role", "tabpanel");
      expect(panel).toHaveAttribute("aria-labelledby", one.id);
    }
    expect(screen.getByRole("tabpanel", { name: "The first way" })).toBeVisible();
    // The panel of the other is on the page, so that its tab names something, and is not drawn.
    expect(document.getElementById(tab("The second way").getAttribute("aria-controls") ?? "")).not.toBeVisible();
    expect(screen.queryByRole("tabpanel", { name: "The second way" })).toBeNull();
  });

  test("test_a_press_chooses_a_tab_shows_its_panel_and_leaves_the_focus_on_the_tab", async () => {
    const heard: Id[] = [];
    render(<Held heard={(id) => heard.push(id)} />);

    await user().click(tab("The second way"));

    expect(heard).toEqual(["two"]);
    expect(tabs().map((one) => one.getAttribute("aria-selected"))).toEqual(["false", "true"]);
    expect(screen.getByRole("tabpanel", { name: "The second way" })).toBeVisible();
    expect(screen.queryByRole("tabpanel", { name: "The first way" })).toBeNull();
    expect(tab("The second way")).toHaveFocus();
  });

  test("test_a_press_on_the_tab_that_is_chosen_changes_nothing", async () => {
    const heard: Id[] = [];
    render(<Held heard={(id) => heard.push(id)} />);

    await user().click(tab("The first way"));

    expect(heard).toEqual([]);
    expect(tab("The first way")).toHaveAttribute("aria-selected", "true");
  });

  test("test_the_arrow_keys_move_between_the_tabs_and_go_round_at_either_end", async () => {
    render(<Held ways={THREE} />);
    const at = () => tabs().map((one) => one.getAttribute("aria-selected") === "true");
    tab("The first way").focus();

    await user().keyboard("{ArrowRight}");
    expect(at()).toEqual([false, true, false]);
    expect(tab("The second way")).toHaveFocus();

    await user().keyboard("{ArrowRight}{ArrowRight}");
    expect(at()).toEqual([true, false, false]);
    expect(tab("The first way")).toHaveFocus();

    await user().keyboard("{ArrowLeft}");
    expect(at()).toEqual([false, false, true]);
    expect(tab("The third way")).toHaveFocus();
  });

  test("test_home_and_end_go_to_the_first_and_the_last", async () => {
    render(<Held ways={THREE} />);
    tab("The first way").focus();

    await user().keyboard("{End}");
    expect(tab("The third way")).toHaveFocus();
    expect(tab("The third way")).toHaveAttribute("aria-selected", "true");

    await user().keyboard("{Home}");
    expect(tab("The first way")).toHaveFocus();
    expect(tab("The first way")).toHaveAttribute("aria-selected", "true");
  });

  test("test_a_key_that_is_held_with_another_is_the_browsers_own_and_moves_no_tab", async () => {
    // Alt and an arrow goes back a page, and a person who presses it means that.
    render(<Held />);
    tab("The first way").focus();

    await user().keyboard("{Alt>}{ArrowRight}{/Alt}");

    expect(tab("The first way")).toHaveAttribute("aria-selected", "true");
  });

  test("test_tab_goes_from_the_chosen_tab_into_its_panel_and_never_to_the_other_tab", async () => {
    render(<Held />);
    const person = user();

    await person.tab();
    expect(tab("The first way")).toHaveFocus();
    await person.tab();
    expect(screen.getByRole("button", { name: "inside The first way" })).toHaveFocus();

    // And back: the keyboard comes to the tab that is chosen, whichever that is.
    await person.click(tab("The second way"));
    await person.tab();
    expect(screen.getByRole("button", { name: "inside The second way" })).toHaveFocus();
    await person.tab({ shift: true });
    expect(tab("The second way")).toHaveFocus();
    expect(tabs().map((one) => one.getAttribute("tabindex"))).toEqual(["-1", "0"]);
  });

  test("test_as_it_is_built_the_first_is_chosen_and_the_panel_of_the_other_is_hidden", () => {
    const built = document.createElement("div");
    built.innerHTML = renderToStaticMarkup(<Held />);
    const page = within(built);

    expect(page.getAllByRole("tab", { hidden: true }).map((one) => one.getAttribute("aria-selected"))).toEqual(["true", "false"]);
    const panels = [...built.querySelectorAll("[role='tabpanel']")];
    expect(panels.map((panel) => panel.hasAttribute("hidden"))).toEqual([false, true]);
  });

  test("test_the_tabs_have_no_accessibility_fault_whichever_is_chosen", async () => {
    const { container } = render(<Held />);
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);

    await user().click(tab("The second way"));
    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("how a tab is drawn", () => {
  test("test_the_chosen_tab_is_of_the_ground_of_its_panel_and_the_other_stands_back_on_sand", () => {
    expect(setBy(".face").get("background-color")).toBe("var(--sand)");
    expect(setBy('.way[aria-selected="true"] > .face').get("background-color")).toBe("var(--page)");
    // The other stands lower, by two pixels of a drawing, and the chosen one stands at its full height.
    expect(setBy(".face").get("margin-block-start")).toBe("calc(var(--px) * 2)");
    expect(setBy('.way[aria-selected="true"] > .face').get("margin-block-start")).toBe("0");
  });

  test("test_the_chosen_tab_joins_its_panel_and_the_other_ends_on_the_rule_of_it", () => {
    // The tabs are laid over the rule of the box under them, as deep as its two rules of
    // ink: the chosen one covers them, and the other ends where they begin.
    expect(setBy(".ways").get("margin-block-end")).toBe("calc(var(--px) * -3)");
    expect(setBy(".face").get("margin-block-end")).toBe("calc(var(--px) * 3)");
    expect(setBy('.way[aria-selected="true"] > .face').get("margin-block-end")).toBe("0");
    // Neither has a rule at its foot: the rule there is the box's own.
    expect(setBy(".face").get("border-block-end")).toBe("0");
    // They are drawn over the box, which is a layer of its own.
    expect(Number(setBy(".ways").get("z-index"))).toBeGreaterThan(1);
  });

  test("test_that_a_tab_is_chosen_is_said_by_more_than_its_colour", () => {
    // It is higher, it joins its panel, it bears a band of amber at its head as what is on
    // does, and it says that it is chosen to whoever hears the page.
    expect(setBy('.way[aria-selected="true"] > .face').get("background-image")).toContain("var(--chosen)");
  });

  test("test_the_button_is_of_one_size_whichever_is_chosen_and_nothing_moves_under_a_press", () => {
    // What is chosen changes the face, inside the button. No rule sets the size or the place
    // of the button by whether it is chosen, in hand or pressed.
    const keyed = RULES.filter((rule) => /\.way\[aria-selected[^\]]*\](?!\s*>)|\.way:(hover|active|focus)/.test(rule.selector));
    const moves = /^(width|height|min-|max-|margin|padding|inset|top|left|right|bottom|font|border-width|flex|order|position|transform)/;

    expect(keyed.flatMap((rule) => [...rule.sets.keys()]).filter((property) => moves.test(property))).toEqual([]);
    // The face of the chosen one is as high as the button. What it gives up of the room
    // about it, it has inside itself, at its head and at its foot: so the button is as high
    // as it was, and the words of the tab stand where they stood.
    const face = setBy(".face");
    const on = setBy('.way[aria-selected="true"] > .face');
    const pixels = (length: string | undefined) => Number(/^calc\(var\(--px\) \* (\d+)\)$/.exec(length ?? "")?.[1] ?? (length === "0" ? 0 : Number.NaN));
    const [above, below] = (on.get("padding-block") ?? "").split(/\s+(?=calc)/);
    const room = (face.get("padding") ?? "").split(/\s+(?=calc)/)[0];
    expect(pixels(on.get("margin-block-start")) + pixels(above)).toBe(pixels(face.get("margin-block-start")) + pixels(room));
    expect(pixels(on.get("margin-block-end")) + pixels(below)).toBe(pixels(face.get("margin-block-end")) + pixels(room));
  });

  test("test_under_a_pointer_the_tab_that_is_not_chosen_is_lit_and_nothing_of_it_moves", () => {
    // It is seen to be a thing to press: its face takes the cream of the chosen one. A
    // finger cannot stand over a thing without pressing it, so it is said of a pointer that can.
    const lit = RULES.filter((rule) => /:hover/.test(rule.selector));

    expect(lit.map((rule) => [rule.under, rule.selector, [...rule.sets]])).toEqual([
      ["@media (hover: hover)", '.way[aria-selected="false"]:hover > .face', [["background-color", "var(--page)"]]],
    ]);
  });

  test("test_every_colour_and_size_is_a_token_and_the_shadow_is_the_shadow_of_the_look", () => {
    const written = RULES.flatMap((rule) => [...rule.sets].map(([property, value]) => ({ rule: rule.selector, property, value })));

    expect(written.filter(({ value }) => /#[0-9a-f]{3,8}\b|rgb|hsl/i.test(value))).toEqual([]);
    expect(written.filter(({ property, value }) => property === "box-shadow" && value !== "var(--box-shadow)" && value !== "none")).toEqual([]);
    expect(written.filter(({ value }) => /dashed|dotted/.test(value))).toEqual([]);
    expect(written.filter(({ property }) => property === "border-radius").map(({ value }) => value)).toEqual(["0"]);
    // A name of the look is set in the face of names, at one of its sizes.
    expect(setBy(".way").get("font")).toBe("400 var(--name-1) / 1 var(--font-name)");
  });

  test("test_with_scripts_off_no_tab_is_drawn_for_none_could_be_pressed", () => {
    const off = RULES.filter((rule) => rule.under === "@media (scripting: none)");

    expect(off.map((rule) => [rule.selector, rule.sets.get("display")])).toEqual([[".ways", "none"]]);
  });

  test("test_with_forced_colours_the_systems_own_colours_carry_the_tab", () => {
    const forced = RULES.filter((rule) => rule.under === "@media (forced-colors: active)");

    expect(forced.length).toBeGreaterThan(0);
    expect(forced.flatMap((rule) => [...rule.sets.values()]).filter((value) => /var\(--(ink|page|sand|chosen|border)\)/.test(value))).toEqual([]);
    // A rule of the page's own that a sheet loaded later might undo weighs more than a class.
    expect(weightOf('.way[aria-selected="true"] > .face')[1]).toBeGreaterThan(weightOf(".face")[1]);
  });
});
