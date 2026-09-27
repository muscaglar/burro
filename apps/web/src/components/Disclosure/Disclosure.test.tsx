import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";

import { faultsIn } from "../../../test/support/axe";
import { asWritten } from "../../../test/support/contrast";
import { heavier, rulesOf, weightOf } from "../../../test/support/css";
import { isDrawn, sizeOf } from "../kit/drawings";
import { Disclosure } from "./Disclosure";
import { BAR_AT_REST, BAR_AT_REST_ON } from "./look";

const user = () => userEvent.setup({ delay: null });

describe("a disclosure", () => {
  test("test_it_is_closed_at_first_and_what_is_inside_is_not_on_the_page", () => {
    render(<Disclosure label="More">inside</Disclosure>);

    expect(screen.getByRole("button", { name: "More" })).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByText("inside")).toBeNull();
  });

  test("test_the_button_opens_it_in_place_and_says_which_part_it_shows", async () => {
    render(<Disclosure label="More">inside</Disclosure>);
    const button = screen.getByRole("button", { name: "More" });

    await user().click(button);

    expect(button).toHaveAttribute("aria-expanded", "true");
    expect(document.getElementById(button.getAttribute("aria-controls") ?? "")).toHaveTextContent("inside");
    expect(button).toHaveFocus();
  });

  test("test_nothing_appears_on_hover_alone", async () => {
    render(<Disclosure label="More">inside</Disclosure>);

    await user().hover(screen.getByRole("button", { name: "More" }));

    expect(screen.queryByText("inside")).toBeNull();
  });

  test("test_it_stays_open_until_it_is_closed", async () => {
    render(
      <>
        <Disclosure label="More">inside</Disclosure>
        <button type="button">elsewhere</button>
      </>,
    );
    const press = user();

    await press.click(screen.getByRole("button", { name: "More" }));
    await press.click(screen.getByRole("button", { name: "elsewhere" }));
    expect(screen.getByText("inside")).toBeInTheDocument();

    await press.click(screen.getByRole("button", { name: "More" }));
    expect(screen.queryByText("inside")).toBeNull();
  });

  test("test_escape_closes_it_and_puts_the_focus_back_on_its_button", async () => {
    render(
      <Disclosure label="More">
        <button type="button">inside</button>
      </Disclosure>,
    );
    const press = user();
    await press.click(screen.getByRole("button", { name: "More" }));
    await press.tab();
    expect(screen.getByRole("button", { name: "inside" })).toHaveFocus();

    await press.keyboard("{Escape}");

    expect(screen.queryByRole("button", { name: "inside" })).toBeNull();
    expect(screen.getByRole("button", { name: "More" })).toHaveFocus();
  });

  test("test_escape_closes_the_innermost_one_and_leaves_the_one_that_holds_it", async () => {
    render(
      <Disclosure label="Outer">
        <Disclosure label="Inner">
          <button type="button">deep</button>
        </Disclosure>
      </Disclosure>,
    );
    const press = user();
    await press.click(screen.getByRole("button", { name: "Outer" }));
    await press.click(screen.getByRole("button", { name: "Inner" }));

    await press.keyboard("{Escape}");

    expect(screen.queryByRole("button", { name: "deep" })).toBeNull();
    expect(screen.getByRole("button", { name: "Outer" })).toHaveAttribute("aria-expanded", "true");
  });

  test("test_the_page_can_decide_whether_it_is_open", async () => {
    const onToggle = jest.fn();
    const { rerender } = render(
      <Disclosure label="More" open={false} onToggle={onToggle}>
        inside
      </Disclosure>,
    );

    await user().click(screen.getByRole("button", { name: "More" }));
    expect(onToggle).toHaveBeenCalledWith(true);
    expect(screen.queryByText("inside")).toBeNull();

    rerender(
      <Disclosure label="More" open onToggle={onToggle}>
        inside
      </Disclosure>,
    );
    expect(screen.getByText("inside")).toBeInTheDocument();
  });

  test("test_a_main_one_and_a_small_one_each_take_a_target_size", () => {
    render(
      <>
        <Disclosure label="Main">a</Disclosure>
        <Disclosure label="Small" size="small" name="Small, of this">
          b
        </Disclosure>
      </>,
    );

    expect(screen.getByRole("button", { name: "Main" })).toHaveClass("target");
    expect(screen.getByRole("button", { name: "Small, of this" })).toHaveClass("target-min");
  });

  test("test_open_or_closed_it_has_no_accessibility_fault", async () => {
    const { container } = render(<Disclosure label="More">inside</Disclosure>);
    expect(await faultsIn(container)).toEqual([]);

    await user().click(screen.getByRole("button", { name: "More" }));
    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("a fold that stands at the foot of what it is seen through", () => {
  /**
   * Stands a fold at the foot of a box that scrolls in itself, as the column of the map is
   * beside the answer, with what it opens under the foot of the box. jsdom lays nothing
   * out, and scrolls nothing.
   */
  function inAColumn(fold: React.ReactNode) {
    const measure = jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (
      this: HTMLElement,
    ) {
      const [top, foot] =
        this.tagName === "BUTTON" ? [833, 880] : this.hasAttribute("data-column") ? [16, 884] : [896, 6659];
      return { top, bottom: foot, left: 0, right: 0, x: 0, y: top, width: 0, height: foot - top, toJSON: () => ({}) };
    });
    const high = window.innerHeight;
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 900 });
    const view = render(
      <div data-column="" style={{ overflowY: "auto" }}>
        {fold}
      </div>,
    );
    const column = view.container.firstElementChild as HTMLElement;
    Object.defineProperty(column, "clientHeight", { configurable: true, value: 868 });
    // It holds more than it shows once the fold is open, and scrolls.
    Object.defineProperty(column, "scrollHeight", { configurable: true, get: () => (column.querySelector("[aria-expanded='true']") ? 6685 : 868) });
    return {
      column,
      putBack: () => {
        measure.mockRestore();
        Object.defineProperty(window, "innerHeight", { configurable: true, value: high });
      },
    };
  }

  test("test_a_fold_that_is_told_to_brings_what_it_opens_into_sight", async () => {
    // Seen at 1440 by 900: "Table of all areas" stood at the foot of the column of the map,
    // and the table it opened began under the foot of the column, out of sight. The button
    // turned amber, and nothing else was seen to happen.
    const { column, putBack } = inAColumn(
      <Disclosure label="More" bring>
        inside
      </Disclosure>,
    );
    try {
      await user().click(screen.getByRole("button", { name: "More" }));

      expect(screen.getByText("inside")).toBeInTheDocument();
      // What it opened is brought up in the column, and the button is never taken over
      // the top of it. How far is what brings a thing into sight to say, and its own test holds it.
      expect(column.scrollTop).toBeGreaterThan(0);
      expect(column.scrollTop).toBeLessThanOrEqual(833 - 8 - 16);
      expect(screen.getByRole("button", { name: "More" })).toHaveFocus();
    } finally {
      putBack();
    }
  });

  test("test_a_fold_that_is_not_told_to_moves_nothing_as_it_did", async () => {
    const { column, putBack } = inAColumn(<Disclosure label="More">inside</Disclosure>);
    try {
      await user().click(screen.getByRole("button", { name: "More" }));

      expect(screen.getByText("inside")).toBeInTheDocument();
      expect(column.scrollTop).toBe(0);
    } finally {
      putBack();
    }
  });

  test("test_nothing_is_moved_as_it_closes_or_where_the_page_draws_it_open", async () => {
    const { column, putBack } = inAColumn(
      <Disclosure label="More" bring openAtFirst>
        inside
      </Disclosure>,
    );
    try {
      expect(screen.getByText("inside")).toBeInTheDocument();
      expect(column.scrollTop).toBe(0);

      await user().click(screen.getByRole("button", { name: "More" }));

      expect(screen.queryByText("inside")).toBeNull();
      expect(column.scrollTop).toBe(0);
    } finally {
      putBack();
    }
  });

  test("test_where_the_page_decides_it_is_brought_into_sight_once_the_page_has_opened_it", async () => {
    function Held() {
      const [open, setOpen] = useState(false);
      return (
        <Disclosure label="More" bring open={open} onToggle={setOpen}>
          inside
        </Disclosure>
      );
    }
    const { column, putBack } = inAColumn(<Held />);
    try {
      await user().click(screen.getByRole("button", { name: "More" }));

      expect(screen.getByText("inside")).toBeInTheDocument();
      expect(column.scrollTop).toBeGreaterThan(0);
      expect(column.scrollTop).toBeLessThanOrEqual(833 - 8 - 16);
    } finally {
      putBack();
    }
  });
});

describe("how a fold is drawn", () => {
  const RULES = rulesOf(readFileSync(path.join(__dirname, "Disclosure.module.css"), "utf8"));
  const FORCED = /forced-colors:\s*active/;
  const DRAWN = RULES.filter((rule) => !FORCED.test(rule.under ?? ""));
  const setsOf = (selector: string) => new Map(DRAWN.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));
  /** The drawing a button is handed, as the page names it: `url("/art/ui-arrow.png")` gives `ui-arrow`. */
  const handed = (button: HTMLElement, token: string) => /\/art\/([a-z0-9-]+)\.png/.exec(button.style.getPropertyValue(token))?.[1] ?? "";

  test("test_the_arrow_of_a_fold_is_town_maps_and_is_shown_at_its_own_size", () => {
    render(<Disclosure label="More">inside</Disclosure>);
    const button = screen.getByRole("button", { name: "More" });
    const mark = setsOf(".bar .mark::before");

    expect(handed(button, "--arrow")).toBe("ui-arrow");
    expect(isDrawn(handed(button, "--arrow"))).toBe(true);
    expect([button.style.getPropertyValue("--arrow-w"), button.style.getPropertyValue("--arrow-h")]).toEqual([
      String(sizeOf("ui-arrow").width),
      String(sizeOf("ui-arrow").height),
    ]);
    // At its own size times the art pixel, with a hard edge: never stretched, never at a fraction.
    expect(mark.get("background")).toBe(
      "var(--arrow) 0 0 / calc(var(--px) * var(--arrow-w)) calc(var(--px) * var(--arrow-h)) no-repeat",
    );
    expect([mark.get("width"), mark.get("height")]).toEqual([
      "calc(var(--px) * var(--arrow-w))",
      "calc(var(--px) * var(--arrow-h))",
    ]);
    expect(mark.get("image-rendering")).toBe("pixelated");
    // It says nothing to a screen reader: the button says whether it is open.
    expect(button.querySelector("[aria-hidden='true']")).toBeEmptyDOMElement();
  });

  test("test_every_fold_that_is_a_bar_is_drawn_one_way_whether_it_stands_alone_or_in_a_stack", () => {
    // Walked: a thing that opens was drawn four ways, each by the page that held it. The
    // founder asked for one thing: "place the arrow to the right of the button and make it
    // clearer that they are collapsable accordion sections".
    render(
      <>
        <Disclosure label="Table of all areas">a</Disclosure>
        <Disclosure label="Budget and home" size="bar">
          b
        </Disclosure>
      </>,
    );
    const [alone, stacked] = [screen.getByRole("button", { name: "Table of all areas" }), screen.getByRole("button", { name: "Budget and home" })];

    // Each is a bar, and no fold is drawn as the button of the kit is any more.
    expect(alone).toHaveClass("button", "bar", "alone", "target");
    expect(stacked).toHaveClass("button", "bar", "target");
    expect(stacked).not.toHaveClass("alone");
    expect(DRAWN.filter((rule) => /\.key\b/.test(rule.selector))).toEqual([]);
    expect(DRAWN.filter((rule) => [...rule.sets.keys()].some((property) => /^border-image/.test(property))).map((rule) => rule.selector)).toEqual([
      ".boxed[aria-expanded=\"true\"]::before",
      ".fold[open] > .boxed::before",
    ]);
    // What each holds is laid out the same: its arrow, and what is read on it.
    for (const bar of [alone, stacked]) {
      const said = bar.firstElementChild as HTMLElement;
      expect([...said.children].map((part) => part.className)).toEqual(["mark", "told"]);
      expect(said.querySelector(".told > .named")?.textContent).toBe(bar.textContent);
    }
  });

  test("test_the_arrow_of_a_bar_stands_at_its_far_end_and_is_still_the_first_thing_in_it_that_says_nothing", () => {
    render(
      <>
        <Disclosure label="Table of all areas">a</Disclosure>
        <Disclosure label="Budget and home" size="bar">
          b
        </Disclosure>
      </>,
    );

    for (const name of ["Table of all areas", "Budget and home"]) {
      const button = screen.getByRole("button", { name });
      expect([name, button.getAttribute("data-arrow")]).toEqual([name, "end"]);
      // It is laid out last and comes first in the page, as it did: it is kept from whoever
      // hears the page, and what the button says is heard as it was.
      expect(button.firstElementChild?.firstElementChild).toHaveAttribute("aria-hidden", "true");
      expect(button.firstElementChild?.firstElementChild).toBeEmptyDOMElement();
    }
    expect(setsOf(".bar .mark").get("order")).toBe("1");
    // What the button says is as wide as the button, so that the end of the one is the end of the other.
    expect([setsOf(".bar > .says").get("flex"), setsOf(".told").get("flex")]).toEqual(["1 1 auto", "1 1 auto"]);
    // Nothing chooses another place for it: the founder asked for this one.
    expect(DRAWN.filter((rule) => /data-arrow/.test(rule.selector))).toEqual([]);
  });

  test("test_the_arrow_points_down_while_a_fold_is_closed_and_up_while_it_is_open_and_turns_in_one_step", () => {
    // The drawing points up. Turned half way round it points down, and every pixel of it is whole.
    expect(setsOf(".bar .mark::before").get("transform")).toBe("rotate(180deg)");
    expect(setsOf('.bar[aria-expanded="true"] .mark::before').get("transform")).toBe("none");
    // The browser's own fold says that it is open by itself, and its bar is turned by that.
    expect(setsOf(".fold[open] > .bar .mark::before").get("transform")).toBe("none");
    // The head of a small one is drawn pointing right, and is turned a quarter to point down.
    expect(setsOf(".small .mark::before").has("transform")).toBe(false);
    expect(setsOf('.small[aria-expanded="true"] .mark::before').get("transform")).toBe("rotate(90deg)");
    expect(setsOf(".fold[open] > .small .mark::before").get("transform")).toBe("rotate(90deg)");
    // Turned over time, a drawing in pixels is for a moment no drawing in pixels: so it is turned at once.
    const moving = RULES.filter((rule) => [...rule.sets.keys()].some((property) => /^(transition|animation)/.test(property)));
    expect(moving.map((rule) => rule.selector)).toEqual([]);
  });

  test("test_a_small_fold_keeps_its_mark_before_its_words", () => {
    render(
      <Disclosure label="Source" size="small">
        inside
      </Disclosure>,
    );
    const button = screen.getByRole("button", { name: "Source" });

    // It stands in a sentence: a mark at the end of its words would stand in the middle of the line.
    expect(button).not.toHaveAttribute("data-arrow");
    expect(button).not.toHaveClass("bar");
    expect(DRAWN.filter((rule) => /\.small\b/.test(rule.selector) && (rule.sets.has("order") || rule.sets.has("margin-inline-start")))).toEqual([]);
  });

  test("test_the_room_of_the_arrow_is_of_one_size_open_or_closed_so_that_nothing_moves_as_it_turns", () => {
    const ROOM = /^(width|height|min-.*|max-.*|padding.*|margin.*|border|border-width|border-style|border-image|font.*|line-height|display|position|inset.*|gap|flex.*)$/;
    const states = DRAWN.filter((rule) => /\[aria-expanded|\[open\]|:hover|:focus|:active/.test(rule.selector));
    const moved = states.flatMap((rule) => [...rule.sets.keys()].filter((property) => ROOM.test(property)).map((property) => `${rule.selector} sets ${property}`));

    expect(states.length).toBeGreaterThan(12);
    expect(moved).toEqual([]);
  });

  test("test_a_bar_that_stands_alone_has_an_edge_of_ink_and_the_hard_shadow_of_the_look", () => {
    render(<Disclosure label="More">inside</Disclosure>);
    const button = screen.getByRole("button", { name: "More" });
    const alone = setsOf(".alone");

    // No stack gives it a rule, and it stands as a chip stands: with the shadow of the look,
    // which one line of the tokens takes away from every one.
    expect(alone.get("border")).toBe("var(--px) solid var(--ink)");
    expect(alone.get("box-shadow")).toContain("var(--box-shadow)");
    expect(alone.get("box-shadow")).toContain("inset 0 calc(var(--px) * -1) 0 var(--sand)");
    // It is as wide as what it says, unless a page lays it out wider.
    expect([alone.get("display"), alone.get("width")]).toEqual(["inline-flex", "auto"]);
    // It is handed the arrow and no picture of a button: it is no button of the kit.
    expect([handed(button, "--art"), handed(button, "--art-down")]).toEqual(["", ""]);
    // It says that it is open as it always did, and does not say that it is pressed.
    expect(button).toHaveAttribute("aria-expanded", "false");
    expect(button).not.toHaveAttribute("aria-pressed");
    // It is told from one of a stack by nothing a test of a page counts bars by.
    expect(button).not.toHaveAttribute("data-rest");
  });

  test("test_a_bar_that_stands_alone_is_amber_while_it_is_open_and_keeps_its_shadow", async () => {
    render(<Disclosure label="More">inside</Disclosure>);
    const button = screen.getByRole("button", { name: "More" });
    await user().click(button);

    expect(button).toHaveAttribute("aria-expanded", "true");
    // The ground of every bar that is open, which a bar that stands alone has as any bar.
    expect(setsOf('.bar[aria-expanded="true"]').get("background-color")).toBe("var(--chosen)");
    for (const open of ['.alone[aria-expanded="true"]', ".fold[open] > .alone", '.alone[aria-expanded="true"]:active', ".fold[open] > .alone:active"]) {
      expect([open, [...setsOf(open).keys()]]).toEqual([open, ["box-shadow"]]);
      expect([open, setsOf(open).get("box-shadow")?.includes("var(--box-shadow)")]).toEqual([open, true]);
    }
  });

  test("test_under_a_press_what_stands_on_the_face_steps_with_it_and_the_button_stays_where_it_is", async () => {
    render(<Disclosure label="More">inside</Disclosure>);
    const button = screen.getByRole("button", { name: "More" });
    const stepping = DRAWN.filter((rule) => rule.sets.has("transform") && /:active\b/.test(rule.selector));

    // The arrow and the words stand on the face, which is inside the button and is no control.
    const face = button.firstElementChild as HTMLElement;
    expect(button.children).toHaveLength(1);
    expect(face.tagName).toBe("SPAN");
    expect(face.textContent).toBe("More");
    expect(face.firstElementChild).toHaveAttribute("aria-hidden", "true");
    // It steps one art pixel down and one to the right, only under a press, and only where movement is welcome.
    expect(stepping.map((rule) => [rule.selector, rule.sets.get("transform"), /prefers-reduced-motion:\s*no-preference/.test(rule.under ?? "")])).toEqual([
      // Seen in a browser: the whole of what a bar says stepped, the cell of its arrow with
      // it, and the cell stood two pixels over the rule under the bar and off its end.
      [".bar:active .drawn", "translate(var(--px), var(--px))", true],
      [".bar:active .told", "translate(var(--px), var(--px))", true],
    ]);
  });

  test("test_a_small_fold_stands_on_a_rule_of_ink_and_is_amber_in_hand_and_while_it_is_open", () => {
    render(
      <Disclosure label="Source" size="small">
        inside
      </Disclosure>,
    );
    const button = screen.getByRole("button", { name: "Source" });
    const small = setsOf(".small");

    // It is handed no picture: it is no button of 44 px, and its mark is drawn by the style sheet.
    expect(button.getAttribute("style")).toBeNull();
    expect([small.get("border"), small.get("border-block-end"), small.get("background")]).toEqual([
      "0",
      "var(--edge) solid var(--ink)",
      "none",
    ]);
    expect(small.get("min-height")).toBe("var(--target-min)");
    for (const state of [".small:hover", ".small:focus-visible", '.small[aria-expanded="true"]', ".fold[open] > .small"]) {
      expect([state, [...setsOf(state)]]).toEqual([
        state,
        [
          ["background-color", "var(--chosen)"],
          ["color", "var(--on-chosen)"],
        ],
      ]);
    }
  });

  test("test_a_fold_that_was_closed_by_a_finger_does_not_stand_on_amber_as_if_it_were_open", () => {
    // On a touch screen what was last pressed is held to be under the pointer until
    // something else is pressed. Amber says that a fold is open: so what the pointer does
    // is drawn only where a pointer can stand over a thing without pressing it.
    const underThePointer = DRAWN.filter((rule) => /:hover\b/.test(rule.selector));

    expect(underThePointer.map((rule) => rule.selector)).toEqual([
      '.bar[aria-expanded="false"]:hover',
      ".fold:not([open]) > .bar:hover",
      '.bar[data-rest="sand"][aria-expanded="false"]:hover',
      '.fold:not([open]) > .bar[data-rest="sand"]:hover',
      '.bar.boxed[aria-expanded="false"]:hover',
      ".fold:not([open]) > .bar.boxed:hover",
      '.boxed[aria-expanded="false"]:hover > .told',
      ".fold:not([open]) > .boxed:hover > .told",
      ".small:hover",
    ]);
    for (const rule of underThePointer) expect([rule.selector, /\(hover:\s*hover\)/.test(rule.under ?? "")]).toEqual([rule.selector, true]);
    // And a bar in hand is never amber, which says that it is open.
    const inHand = DRAWN.filter((rule) => /\.(bar|boxed)\b.*:(hover|focus-visible|active)/.test(rule.selector) && rule.sets.has("background-color"));
    expect(inHand.length).toBeGreaterThan(8);
    expect(inHand.filter((rule) => /chosen|amber/.test(rule.sets.get("background-color") ?? ""))).toEqual([]);
  });

  test("test_a_short_label_is_set_in_the_face_of_names_and_what_is_read_in_the_reading_face", () => {
    render(
      <>
        <Disclosure label="Table of all areas">a</Disclosure>
        <Disclosure label="3 areas are not ranked">b</Disclosure>
        <Disclosure label={<strong>More than words</strong>} name="More than words">
          c
        </Disclosure>
      </>,
    );

    const said = (name: string) => screen.getByRole("button", { name }).firstElementChild;

    expect(said("Table of all areas")).toHaveAttribute("data-reads", "false");
    // A figure is read exactly, whatever it stands in. A label that is more than words is laid out by whoever wrote it.
    expect(said("3 areas are not ranked")).toHaveAttribute("data-reads", "true");
    expect(said("More than words")).toHaveAttribute("data-reads", "true");

    expect([setsOf(".says").get("font"), setsOf(".says").get("font-synthesis")]).toEqual([
      "400 var(--name-1) / 1 var(--font-name)",
      "none",
    ]);
    expect(setsOf('.says[data-reads="true"]').get("font")).toBe("700 var(--size-body) / 1.25 var(--font-say)");
    expect(setsOf('.small > .says[data-reads="true"]').get("font")).toBe("400 var(--size-small) / 1.25 var(--font-say)");
  });

  test("test_the_face_and_the_size_of_what_a_fold_says_are_not_the_buttons_to_set", () => {
    // Seen in the style sheets: a page that lays the button of a fold out sets a size of type
    // on it, for the row it stands in. The face of names is drawn in pixels, and at a size
    // that is not its own no pixel of it is a whole pixel of the screen. So what is said has
    // its face and its size of its own, and the button has none to hand down.
    const ofTheButton = DRAWN.filter((rule) => /^\.(button|alone|small|bar)(\[|:|\.|$)/.test(rule.selector) && !/\s/.test(rule.selector));
    const faces = ofTheButton.filter((rule) => [...rule.sets.keys()].some((property) => /^font/.test(property)));

    expect(ofTheButton.length).toBeGreaterThan(4);
    expect(faces.map((rule) => rule.selector)).toEqual([]);
    for (const size of ["main", "small", "bar"] as const) {
      const { unmount } = render(
        <Disclosure label="More" size={size}>
          inside
        </Disclosure>,
      );
      const button = screen.getByRole("button", { name: "More" });
      // All that the button holds is what it says, which holds the arrow and the words.
      expect([size, button.children.length, button.firstElementChild?.textContent]).toEqual([size, 1, "More"]);
      expect([size, button.firstElementChild?.firstElementChild?.getAttribute("aria-hidden")]).toEqual([size, "true"]);
      unmount();
    }
  });

  test("test_where_the_system_draws_in_its_own_colours_no_shade_is_laid_and_the_arrow_is_cut_from_the_colour_of_words", () => {
    const forced = RULES.filter((rule) => FORCED.test(rule.under ?? ""));
    const of = (selector: string) => new Map(forced.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));

    // The arrow is cut from the colour of the system's words, and no drawing in ink is left on a ground that may be dark.
    expect([of(".bar .mark::before").get("background"), of(".small .mark::before").get("background")]).toEqual(["ButtonText", "ButtonText"]);
    expect(RULES.filter((rule) => (rule.sets.get("border-image") ?? "").trim() === "none")).toEqual([]);
    // A bar of a stack has no edge of its own to say that it is open, and the system lays
    // no shade: so it is drawn in the colours the system gives to what is chosen, and its arrow with it.
    const open = of('.bar[aria-expanded="true"]');
    expect([open.get("background-color"), open.get("color"), open.get("forced-color-adjust")]).toEqual([
      "Highlight",
      "HighlightText",
      "none",
    ]);
    expect(of('.bar[aria-expanded="true"] .mark::before').get("background")).toBe("HighlightText");
    expect(of(".fold[open] > .bar .mark::before").get("background")).toBe("HighlightText");
    expect(of(".bar").get("background-color")).toBe("ButtonFace");
    // One that stands alone keeps its edge, in the colour of the system's words, and throws no shadow.
    expect([of(".alone").get("border-color"), of(".alone").get("box-shadow")]).toEqual(["ButtonText", "none"]);
  });
});

describe("a bar, which is one of a stack of folds", () => {
  const RULES = rulesOf(readFileSync(path.join(__dirname, "Disclosure.module.css"), "utf8"));
  const DRAWN = RULES.filter((rule) => !/forced-colors:\s*active/.test(rule.under ?? ""));
  const setsOf = (selector: string) => new Map(DRAWN.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));

  /** A stack of three, as the groups of the settings are. */
  function stack() {
    return render(
      <div>
        <Disclosure label="Budget and home" size="bar" drawn={<span data-drawing="" aria-hidden="true" />} holds="Renting, up to £1,700 a month" openAtFirst>
          <button type="button">inside</button>
        </Disclosure>
        <Disclosure label="Journeys" size="bar" holds={null}>
          the journeys
        </Disclosure>
        <Disclosure label="Green" size="bar">
          the vibes
        </Disclosure>
      </div>,
    );
  }

  test("test_a_bar_is_a_button_from_edge_to_edge_and_the_whole_of_it_takes_the_press", async () => {
    stack();
    const bar = screen.getByRole("button", { name: "Journeys" });

    // It is the browser's own button, the size of a main control, and all that is on it is inside it.
    expect([bar.tagName, bar.getAttribute("type")]).toEqual(["BUTTON", "button"]);
    expect(bar).toHaveClass("bar", "target");
    expect(bar).not.toHaveClass("alone");
    expect([setsOf(".bar").get("display"), setsOf(".bar").get("width")]).toEqual(["flex", "100%"]);
    // A press anywhere on it opens it: on its name, and on the cell of its arrow.
    await user().click(bar.querySelector("[aria-hidden='true']") as HTMLElement);
    expect(bar).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("the journeys")).toBeInTheDocument();
    await user().click(within(bar).getByText("Journeys"));
    expect(bar).toHaveAttribute("aria-expanded", "false");
  });

  test("test_a_bar_is_drawn_at_the_pixel_of_a_phone_on_every_screen_so_that_it_is_the_same_bar_wherever_it_stands", () => {
    // In the settings every control is drawn so. A bar of another page was drawn at the
    // pixel of the screen, and its arrow was half as large again on a desk.
    expect(setsOf(".bar").get("--px")).toBe("var(--px-small)");
    expect([setsOf(".stacked").get("border-block-end"), setsOf(".stacked:not(.stacked + .stacked)").get("border-block-start")]).toEqual([
      "var(--px-small) solid var(--ink)",
      "var(--px-small) solid var(--ink)",
    ]);
  });

  test("test_the_bars_of_a_stack_stand_one_on_the_next_with_a_rule_of_ink_between_them_and_none_is_dashed", () => {
    const { container } = stack();
    const folds = [...(container.firstElementChild as HTMLElement).children];

    expect(folds.map((fold) => fold.classList.contains("stacked"))).toEqual([true, true, true]);
    expect(setsOf(".stacked").get("border-block-end")).toBe("var(--px-small) solid var(--ink)");
    // The first of a stack has a rule over it too, wherever the stack stands.
    expect(setsOf(".stacked:not(.stacked + .stacked)").get("border-block-start")).toBe("var(--px-small) solid var(--ink)");
    // What a bar opens stands directly under it, parted from it by a rule, which is of what
    // was opened: the bar is as high open as closed.
    expect([...setsOf(".stacked > .bar + *")]).toEqual([
      ["margin-block-start", "0"],
      ["border-block-start", "var(--px-small) solid var(--ink)"],
    ]);
    expect(heavier(weightOf(".stacked > .bar + *"), weightOf(".panel"))).toBe(true);
    // A bar has no edge of its own, and no room between it and the next.
    expect([setsOf(".bar").get("border"), setsOf(".stacked").has("margin"), setsOf(".stacked").has("gap")]).toEqual(["0", false, false]);
  });

  test("test_a_bar_that_is_open_is_amber_and_is_told_from_one_that_is_closed_by_its_arrow_as_well", async () => {
    stack();
    const [open, closed] = [screen.getByRole("button", { name: "Budget and home" }), screen.getByRole("button", { name: "Green" })];

    expect([open.getAttribute("aria-expanded"), closed.getAttribute("aria-expanded")]).toEqual(["true", "false"]);
    const amber = setsOf('.bar[aria-expanded="true"]');
    expect([amber.get("background-color"), amber.get("color")]).toEqual(["var(--chosen)", "var(--on-chosen)"]);
    // The browser's own fold is amber while it is open, by the same rule.
    expect([...setsOf(".fold[open] > .bar")]).toEqual([...amber]);
    // Closed it is cream, as the plain button of the look is: amber is told from cream more easily than from sand.
    expect(BAR_AT_REST).toBe("page");
    expect(closed).toHaveAttribute("data-rest", "page");
    expect(setsOf(".bar").get("background-color")).toBe("var(--page)");
    // Its shade lies along its foot, in sand, and in poppy where it is amber: as the button's does.
    expect([setsOf(".bar").get("box-shadow"), amber.get("box-shadow")]).toEqual([
      "inset 0 calc(var(--px) * -1) 0 var(--sand)",
      "inset 0 calc(var(--px) * -1) 0 var(--poppy)",
    ]);
    // Amber is not told from cream by everyone: the arrow points down at what would open, and up once it has.
    expect(setsOf(".bar .mark::before").get("transform")).toBe("rotate(180deg)");
    expect(setsOf('.bar[aria-expanded="true"] .mark::before').get("transform")).toBe("none");
  });

  test("test_a_bar_may_stand_on_sand_while_it_is_closed_as_town_map_drew_its_drawers_by_one_line", () => {
    expect(BAR_AT_REST_ON).toEqual(["page", "sand"]);
    render(
      <Disclosure label="Green" size="bar" rest="sand">
        the vibes
      </Disclosure>,
    );

    expect(screen.getByRole("button", { name: "Green" })).toHaveAttribute("data-rest", "sand");
    expect([...setsOf('.bar[data-rest="sand"]')]).toEqual([
      ["background-color", "var(--sand)"],
      ["box-shadow", "none"],
    ]);
    // Open it is amber whichever it stood on, in hand as out of it: what is said of a bar
    // in hand, and of one on sand, is said of a bar that is closed and of no other.
    const ground = DRAWN.filter((rule) => /^\.bar\b/.test(rule.selector) && !/\s/.test(rule.selector) && !/boxed/.test(rule.selector) && rule.sets.has("background-color"));
    expect(ground.map((rule) => rule.selector).sort()).toEqual(
      [
        ".bar",
        '.bar[data-rest="sand"]',
        '.bar[aria-expanded="false"]:active',
        '.bar[data-rest="sand"][aria-expanded="false"]:active',
        '.bar[aria-expanded="false"]:focus-visible',
        '.bar[data-rest="sand"][aria-expanded="false"]:focus-visible',
        '.bar[aria-expanded="false"]:hover',
        '.bar[data-rest="sand"][aria-expanded="false"]:hover',
        '.bar[aria-expanded="true"]',
      ].sort(),
    );
    expect(heavier(weightOf('.bar[aria-expanded="true"]'), weightOf(".bar"))).toBe(true);
    // A bar on sand that is open: the two rules weigh the same, and the later is of the open bar.
    const written = DRAWN.map((rule) => rule.selector);
    expect(written.indexOf('.bar[aria-expanded="true"]')).toBeGreaterThan(written.indexOf('.bar[data-rest="sand"]'));
  });

  test("test_the_arrow_of_a_bar_stands_in_a_cell_at_its_very_end_which_is_as_high_as_the_bar", () => {
    const cell = setsOf(".bar .mark");

    // Sand, behind a rule of ink, as the cross of a chip stands: it is seen to be what is pressed.
    expect([cell.get("background-color"), cell.get("border-inline-start"), cell.get("align-self")]).toEqual([
      "var(--sand)",
      "var(--px) solid var(--ink)",
      "stretch",
    ]);
    expect(cell.has("height")).toBe(false);
    // A whole number of art pixels wide, with the arrow in the middle of it on whole pixels.
    const arrow = sizeOf("ui-arrow").width;
    expect(cell.get("width")).toBe("calc(var(--px) * (var(--arrow-w) + 13))");
    expect((arrow + 13 - 1 - arrow) % 2).toBe(0);
    expect([cell.get("display"), cell.get("place-items")]).toEqual(["grid", "center"]);
    // No narrower than a control is, at the pixel a bar is drawn at.
    expect((arrow + 13) * 2).toBeGreaterThanOrEqual(44);
    // The bar keeps no room at its far side: the cell ends where the bar does.
    expect(setsOf(".bar").get("padding-inline")).toBe("var(--bar-begins) 0");
  });

  test("test_what_a_bar_says_begins_five_art_pixels_in_unless_whatever_lays_the_fold_out_says_where", () => {
    // What a bar says begins where what it opens begins, and a page knows where that is.
    const given = RULES.filter((rule) => rule.sets.has("--bar-begins"));

    expect(given.map((rule) => [rule.selector, rule.under, rule.sets.get("--bar-begins")])).toEqual([
      [":where(.disclosure)", null, "calc(var(--px-small) * 5)"],
      [":where(.fold)", null, "calc(var(--px-small) * 5)"],
    ]);
    // It is said with no weight, so that whatever a page says of it weighs more, whichever sheet is read last.
    for (const { selector } of given) expect([selector, weightOf(selector)]).toEqual([selector, [0, 0, 0]]);
    // And of every fold: one inside another begins where a fold begins.
    expect(setsOf(".bar").get("padding-inline")).toBe("var(--bar-begins) 0");
    expect(setsOf(".boxed > .told").get("padding-inline")).toBe("var(--bar-begins) calc(var(--px) * 4)");
  });

  test("test_what_a_bar_holds_is_said_on_it_and_describes_the_button_and_is_no_part_of_its_name", () => {
    stack();
    const bar = screen.getByRole("button", { name: "Budget and home" });

    // Whoever looks for the bar by its name finds it, whatever it holds.
    expect(bar).toHaveAccessibleName("Budget and home");
    expect(bar).toHaveAccessibleDescription("Renting, up to £1,700 a month");
    // It is on the page for everyone, on the bar itself, and not for a screen reader alone.
    const held = within(bar).getByText("Renting, up to £1,700 a month");
    expect(held).toBeVisible();
    expect(held.closest(".visually-hidden, [aria-hidden='true'], [hidden]")).toBeNull();
    // It holds a figure, and is read: in the reading face, whatever the name is set in.
    expect(setsOf(".holds").get("font")).toBe("400 var(--size-small) / calc(var(--size-small) * 4 / 3) var(--font-say)");
    // The drawing is dress, and stands before the name.
    expect(bar.querySelector("[data-drawing]")?.closest(".drawn")).not.toBeNull();
    expect(bar.querySelector("[data-drawing]")?.compareDocumentPosition(within(bar).getByText("Budget and home")) ?? 0).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    );
  });

  test("test_what_a_bar_holds_is_set_on_lines_of_whole_pixels_so_that_a_bar_that_comes_to_say_more_grows_by_whole_pixels", () => {
    // Measured in a browser at 390 by 844: a bar that came to say what its group held grew
    // by 21.5 px, a line of 19.5 and the room over it. What was pressed under the bar is
    // held where it stands by the page going by as much, and a page goes by whole pixels:
    // so it stood half a pixel from where it had stood.
    const [, size, line] = /^400 (\S+) \/ (calc\(.*\)) var\(--font-say\)$/.exec(setsOf(".holds").get("font") ?? "") ?? [];

    // A length, of four thirds of the size of its words: worked out once, and whole.
    expect([size, line]).toEqual(["var(--size-small)", "calc(var(--size-small) * 4 / 3)"]);
    // The small size is 15 px to the 16 of the page, which the tokens say: a line of it is 20.
    expect(asWritten()["--size-small"]).toBe("0.9375rem");
    expect((0.9375 * 16 * 4) / 3).toBe(20);
    // And the room between its name and what it holds is whole art pixels.
    expect(setsOf(".told").get("gap")).toBe("var(--px) calc(var(--px) * 6)");
  });

  test("test_a_bar_says_nothing_of_what_it_holds_where_nothing_is_set", () => {
    stack();

    for (const name of ["Journeys", "Green"]) {
      const bar = screen.getByRole("button", { name });
      expect([name, bar.textContent]).toEqual([name, name]);
      expect(bar).not.toHaveAttribute("aria-describedby");
      expect(bar).not.toHaveAttribute("aria-labelledby");
      expect(bar.querySelector(".holds")).toBeNull();
    }
  });

  test("test_a_name_that_is_given_to_a_bar_is_its_name_and_what_it_holds_still_describes_it", () => {
    render(
      <Disclosure label="Green" name="Green, of the settings" size="bar" holds="Leafy">
        the vibes
      </Disclosure>,
    );
    const bar = screen.getByRole("button", { name: "Green, of the settings" });

    expect(bar).not.toHaveAttribute("aria-labelledby");
    expect(bar).toHaveAccessibleDescription("Leafy");
  });

  test("test_what_a_bar_holds_stands_beside_its_name_where_there_is_room_and_under_it_where_there_is_none", () => {
    const told = setsOf(".told");

    // Nobody is asked how wide the bar is: what it holds asks for the room it needs.
    expect([told.get("display"), told.get("flex-wrap")]).toEqual(["flex", "wrap"]);
    expect(setsOf(".holds").get("flex")).toBe("1 1 12rem");
    // No rule of a fold asks how wide the window is: a fold stands in a column as in a page.
    expect(RULES.filter((rule) => /@(media|container)[^{]*\b(width|height)\b/.test(rule.under ?? "")).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_a_bar_is_of_one_size_open_or_closed_in_hand_or_not", () => {
    const ROOM = /^(width|height|min-.*|max-.*|padding.*|margin.*|border|border-width|border-style|border-block.*|border-inline.*|font.*|line-height|display|position|inset.*|gap|flex.*|order|align.*)$/;
    const states = DRAWN.filter((rule) => /\.(bar|alone|boxed|fold)\b/.test(rule.selector) && /(\[aria-expanded|\[open\]|:hover|:focus|:active)/.test(rule.selector));
    const moved = states.flatMap((rule) => [...rule.sets.keys()].filter((property) => ROOM.test(property)).map((property) => `${rule.selector} sets ${property}`));

    expect(states.length).toBeGreaterThan(20);
    expect(moved).toEqual([]);
  });

  test("test_the_ring_of_the_focus_stands_inside_a_bar_of_a_stack_and_is_whole_on_all_four_sides", () => {
    // Walked by keyboard: the ring of a bar in hand was drawn on three sides, and at the
    // right was hidden by the cell of the arrow, which was a layer of its own over the bar.
    expect(setsOf(".bar:not(.alone, .boxed):focus-visible").get("outline-offset")).toBe("calc(var(--focus-ring) * -1)");
    expect([...setsOf(".bar .mark").keys()].filter((property) => /^(position|z-index|isolation|transform|opacity|filter|will-change)$/.test(property))).toEqual([]);
    expect(setsOf(".bar .mark::before").has("position")).toBe(false);
    // The ring itself is the one every control has: nothing here takes it off or draws another.
    expect(RULES.filter((rule) => ["outline", "outline-style", "outline-width", "outline-color"].some((property) => rule.sets.has(property)))).toEqual([]);
  });

  test("test_escape_closes_a_bar_from_what_it_holds_and_puts_the_focus_back_on_it", async () => {
    stack();
    const press = user();
    const bar = screen.getByRole("button", { name: "Budget and home" });
    screen.getByRole("button", { name: "inside" }).focus();

    await press.keyboard("{Escape}");

    expect(bar).toHaveAttribute("aria-expanded", "false");
    expect(bar).toHaveFocus();
  });

  test("test_a_stack_of_bars_has_no_accessibility_fault", async () => {
    const { container } = stack();

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("every edge of a fold", () => {
  test("test_no_edge_of_a_fold_is_dashed", () => {
    // The founder: "The dashed border is not understood to a user, please make solid".
    const folder = __dirname;
    const written = ["Disclosure.module.css", "Disclosure.tsx", "Summary.tsx", "Folded.tsx", "look.ts"].map((file) => [file, readFileSync(path.join(folder, file), "utf8")] as const);
    const dashed = written.filter(([file, text]) => /\b(dashed|dotted)\b/.test(file.endsWith(".css") ? text.replace(/\/\*[\s\S]*?\*\//g, "") : text));

    expect(dashed.map(([file]) => file)).toEqual([]);
  });
});
