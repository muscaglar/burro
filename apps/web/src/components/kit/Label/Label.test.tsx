import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { faultsIn } from "../../../../test/support/axe";
import { asWritten } from "../../../../test/support/contrast";
import { rulesOf } from "../../../../test/support/css";
import { sizeOf } from "../drawings";
import { THING_STATES, type ThingState } from "../Thing/drawn";
import { Label } from "./Label";
import { ASSUMED_STANDS_ON, GROUNDS, type AssumedStandsOn } from "./look";
import { stateOf } from "./state";

const CSS = readFileSync(path.join(__dirname, "Label.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const ALL = rulesOf(CSS);
const STYLES = ALL.filter((rule) => !/forced-colors/.test(rule.under ?? ""));
/** What the style sheet sets of a selector, each value on one line however it is written. */
const setsOf = (selector: string) =>
  new Map(
    STYLES.filter((rule) => rule.selector === selector).flatMap((rule) =>
      [...rule.sets].map(([property, value]): [string, string] => [property, value.replace(/\s+/g, " ")]),
    ),
  );
/** Each moment of a run of frames of the style sheet, with what it sets. */
const framesOf = (name: string) =>
  [...(new RegExp(`@keyframes ${name}\\s*\\{((?:[^{}]*\\{[^{}]*\\})*)\\s*\\}`).exec(CSS)?.[1] ?? "").matchAll(/([^{}]+)\{([^{}]*)\}/g)].map(
    ([, at, sets]) => [(at ?? "").replace(/\s+/g, " ").trim(), (sets ?? "").replace(/\s+/g, " ").trim()],
  );
const leafy = { kind: "tag", id: "leafy", family: "green" } as const;

describe("a chip", () => {
  test("test_a_press_opens_the_control_of_its_thing", async () => {
    const onOpen = jest.fn();
    const user = userEvent.setup({ delay: null });
    render(<Label thing={leafy} says="Leafy: more" onOpen={onOpen} />);

    await user.click(screen.getByRole("button", { name: "Leafy: more" }));
    expect(onOpen).toHaveBeenCalledTimes(1);

    // By keyboard too: it is a native button.
    await user.keyboard("{Enter}");
    expect(onOpen).toHaveBeenCalledTimes(2);
  });

  test("test_what_is_pressed_is_a_native_button_of_the_size_of_a_main_control", () => {
    render(<Label thing={leafy} says="Leafy: more" onOpen={() => undefined} onTakeOff={() => undefined} />);

    for (const button of screen.getAllByRole("button")) {
      expect(button.tagName).toBe("BUTTON");
      expect(button).toHaveAttribute("type", "button");
      expect(button).toHaveClass("target");
    }
    expect(setsOf(".chip").get("min-height")).toBe("var(--target)");
  });

  test("test_a_page_may_give_the_focus_to_the_button_that_opens", () => {
    const found: { current: HTMLButtonElement | null } = { current: null };
    render(<Label ref={found} thing={leafy} says="Leafy: more" onOpen={() => undefined} onTakeOff={() => undefined} />);

    found.current?.focus();
    expect(screen.getByRole("button", { name: "Leafy: more" })).toHaveFocus();
  });

  test.each<[ThingState, string]>([
    ["said", "Leafy: more"],
    ["assumed", "Leafy: more assumed"],
    ["off", "Leafy: more does not count"],
  ])("test_it_says_what_it_holds_and_then_its_state_in_words: %s", (state, said) => {
    const { container } = render(<Label thing={leafy} says="Leafy: more" state={state} onOpen={() => undefined} />);

    // What is seen is what is heard: the state is drawn in words, where it can be read.
    expect(screen.getByRole("button")).toHaveAccessibleName(said);
    expect(screen.getByRole("button")).toHaveTextContent(said);
    expect(container.firstElementChild).toHaveAttribute("data-state", state);
  });

  test("test_a_state_that_is_true_of_a_part_says_of_which", () => {
    render(
      <Label
        thing={{ kind: "place" }}
        says="Cindermoor Works within 45 minutes, by public transport, flexible"
        state="assumed"
        of="45 minutes, public transport, flexible"
        onOpen={() => undefined}
      />,
    );

    expect(screen.getByText("assumed: 45 minutes, public transport, flexible")).toBeInTheDocument();
    expect(stateOf("assumed", "45 minutes")).toBe("assumed: 45 minutes");
    expect(stateOf("assumed")).toBe("assumed");
    // What a person said has no state to say, of anything.
    expect(stateOf("said", "45 minutes")).toBeNull();
  });

  test("test_words_that_say_the_state_already_are_not_followed_by_it_a_second_time", () => {
    const { container } = render(
      <Label
        thing={{ kind: "budget" }}
        says={
          <>
            <b>£1,700 a month</b>, One bedroom, flexible <i>assumed</i>
          </>
        }
        state="assumed"
        stateSaid
        onOpen={() => undefined}
      />,
    );

    // The word is said once, where the page said it.
    expect(screen.getByRole("button").textContent).toBe("£1,700 a month, One bedroom, flexible assumed");
    expect(container.querySelector(".state")).toBeNull();
    // The chip says its state all the same, to whatever lays it out.
    expect(container.firstElementChild).toHaveAttribute("data-state", "assumed");
  });

  test("test_its_drawing_stands_beside_its_words_and_is_kept_from_a_screen_reader", () => {
    const { container } = render(<Label thing={leafy} says="Leafy: more" onOpen={() => undefined} />);
    const drawing = container.querySelector(".drawing") as HTMLElement | null;

    expect(drawing?.style.getPropertyValue("--art")).toBe('url("/art/thing-leafy.png")');
    expect(drawing?.closest("[aria-hidden='true']")).not.toBeNull();
    expect(screen.queryByRole("img")).toBeNull();
    // The thing comes first, and its words after it.
    expect([...(screen.getByRole("button").children ?? [])].map((part) => part.className)).toEqual(["thing", "words"]);
  });

  test("test_the_cross_takes_the_thing_off_and_says_what_it_takes_off", async () => {
    const onTakeOff = jest.fn();
    const onOpen = jest.fn();
    const user = userEvent.setup({ delay: null });
    render(<Label thing={leafy} says="Leafy: more" named="Leafy" onOpen={onOpen} onTakeOff={onTakeOff} />);

    await user.click(screen.getByRole("button", { name: "Remove: Leafy" }));

    expect(onTakeOff).toHaveBeenCalledTimes(1);
    expect(onOpen).not.toHaveBeenCalled();
  });

  test("test_the_cross_is_named_by_the_words_of_the_chip_where_it_is_given_no_name", () => {
    const { rerender } = render(<Label thing={leafy} says="Leafy: more" onTakeOff={() => undefined} />);
    expect(screen.getByRole("button")).toHaveAccessibleName("Remove: Leafy: more");

    // Words that are no line of text name nothing: the cross then says what it does, and no more.
    rerender(<Label thing={leafy} says={<b>Leafy</b>} onTakeOff={() => undefined} />);
    expect(screen.getByRole("button")).toHaveAccessibleName("Remove");
  });

  test("test_the_cross_is_forty_four_pixels_square_and_is_the_drawing_of_a_cross", () => {
    const { container } = render(<Label thing={leafy} says="Leafy: more" onTakeOff={() => undefined} />);
    const cross = container.querySelector(".cross") as HTMLElement;
    const { width, height } = sizeOf("ui-cross");

    // As wide as a main control, and as high as the chip, which is as high as one at the least.
    expect(setsOf(".off").get("width")).toBe("var(--target)");
    expect(setsOf(".off").get("flex")).toBe("none");
    expect(setsOf(".chip").get("align-items")).toBe("stretch");
    expect(cross.style.getPropertyValue("--art")).toBe('url("/art/ui-cross.png")');
    expect([cross.style.getPropertyValue("--w"), cross.style.getPropertyValue("--h")]).toEqual([String(width), String(height)]);
    expect(cross).toHaveAttribute("aria-hidden", "true");
    expect(setsOf(".cross").get("image-rendering")).toBe("pixelated");
  });

  test("test_a_chip_that_cannot_be_taken_off_has_no_cross", () => {
    render(<Label thing={{ kind: "tenure" }} says="Renting" onOpen={() => undefined} />);

    expect(screen.getAllByRole("button")).toHaveLength(1);
    expect(screen.queryByRole("button", { name: /Remove/ })).toBeNull();
  });

  test("test_what_else_is_pressed_on_a_chip_stands_between_its_words_and_its_cross", () => {
    render(
      <Label
        thing={{ kind: "tag", id: "pace", family: "pace_food" }}
        says="Going out: towards Calm"
        named="Going out"
        onOpen={() => undefined}
        onTakeOff={() => undefined}
        beside={
          <button type="button" className="target" aria-label="Turn Going out towards Buzzy">
            Turn
          </button>
        }
      />,
    );

    expect(screen.getAllByRole("button").map((button) => button.getAttribute("aria-label") ?? button.textContent)).toEqual([
      "Going out: towards Calm",
      "Turn Going out towards Buzzy",
      "Remove: Going out",
    ]);
  });

  test.each(THING_STATES)("test_a_chip_has_a_solid_edge_of_ink_whatever_its_state: %s", (state) => {
    const { container } = render(<Label thing={leafy} says="Leafy: more" state={state} />);

    // A solid edge of ink, one art pixel wide, is what every chip has. What nobody said had
    // a dashed one, and a person who walked the website did not know what it was for.
    expect(setsOf(".chip").get("border")).toBe("var(--px) solid var(--ink)");
    expect(setsOf(".chip").get("background")).toBe("var(--page)");
    // No rule of any state sets the edge of a chip, or takes it away to draw another over it.
    // With forced colours the edge is the colour of the system's words, and as solid.
    const ofAState = STYLES.filter((rule) => /\[data-state/.test(rule.selector));
    expect(ofAState.flatMap((rule) => [...rule.sets.keys()]).filter((property) => /^(border|outline)/.test(property))).toEqual([]);
    // What counts for nothing has its thing in outline, and the edge of a chip a person said.
    expect(container.querySelector(".thing")).toHaveAttribute("data-state", state);
    expect(STYLES.filter((rule) => /\[data-state="(off|said)"\]/.test(rule.selector)).map((rule) => rule.selector)).toEqual([]);
    // Nothing of a chip is marked by an edge, so the thing in it has none either.
    expect(container.querySelector(".thing")).toHaveAttribute("data-edged", "false");
  });

  test("test_no_edge_of_a_chip_is_drawn_in_dashes_or_in_dots_with_forced_colours_as_without", () => {
    // Dashes were drawn in art pixels too, as a run of ink and page that repeats.
    expect(/dashed|dotted|repeating-linear-gradient/.test(CSS)).toBe(false);
    expect(ALL.filter((rule) => rule.sets.get("border-color") === "transparent").map((rule) => rule.selector)).toEqual([]);
    expect(ALL.filter((rule) => rule.sets.has("border-style")).map((rule) => rule.selector)).toEqual([]);
  });

  test.each(THING_STATES)("test_what_nobody_said_is_told_by_its_word_and_the_chip_says_what_it_stands_on: %s", (state) => {
    const { container } = render(<Label thing={leafy} says="Leafy: more" state={state} onOpen={() => undefined} />);

    // The word is what says it, to everyone: a ground alone would say it to some.
    expect(screen.getByRole("button").textContent?.includes("assumed")).toBe(state === "assumed");
    // One line chooses what such a chip stands on, and every chip says which was chosen.
    expect(GROUNDS).toEqual(["page", "sand"]);
    expect(GROUNDS).toContain(ASSUMED_STANDS_ON);
    expect(container.firstElementChild).toHaveAttribute("data-ground", ASSUMED_STANDS_ON);
  });

  test("test_on_sand_a_chip_that_nobody_said_is_lit_the_other_way_in_hand_and_is_amber_while_open", () => {
    const onSand = STYLES.filter((rule) => /\[data-ground/.test(rule.selector));
    const chosen: AssumedStandsOn = "sand";

    expect(onSand.map((rule) => [rule.selector, [...rule.sets]])).toEqual([
      [`.label[data-state="assumed"][data-ground="${chosen}"] .chip`, [["background", "var(--sand)"]]],
      // Sand is what a chip in hand is lit with, so on sand it is lit with page.
      [`.label[data-state="assumed"][data-ground="${chosen}"] .opens:hover`, [["background-color", "var(--page)"]]],
      [`.label[data-state="assumed"][data-ground="${chosen}"] .opens:focus-visible`, [["background-color", "var(--page)"]]],
      // Open, it is amber as every chip is, in hand or not: this weighs as much as what lights it, and comes after.
      [`.label[data-state="assumed"][data-ground="${chosen}"] .opens[aria-expanded="true"]`, [["background-color", "var(--amber)"]]],
    ]);
    // What a person said and what counts for nothing stand on page, whatever the line says.
    expect(onSand.every((rule) => rule.selector.startsWith('.label[data-state="assumed"]'))).toBe(true);
  });

  test("test_with_nothing_to_open_it_is_words_and_no_button", () => {
    render(<Label thing={{ kind: "usual" }} says="Usual settings: 7" />);

    expect(screen.queryByRole("button")).toBeNull();
    expect(screen.getByText("Usual settings: 7")).toBeInTheDocument();
  });

  test("test_a_chip_that_opens_a_control_says_whether_it_is_open_and_is_amber_while_it_is", () => {
    const { rerender } = render(
      <Label thing={leafy} says="Leafy: more" onOpen={() => undefined} open={false} controls="the-control" />,
    );
    expect(screen.getByRole("button")).toHaveAttribute("aria-expanded", "false");
    expect(screen.getByRole("button")).toHaveAttribute("aria-controls", "the-control");

    rerender(<Label thing={leafy} says="Leafy: more" onOpen={() => undefined} open controls="the-control" />);
    expect(screen.getByRole("button")).toHaveAttribute("aria-expanded", "true");
    expect([...setsOf('.opens[aria-expanded="true"]')]).toEqual([["background-color", "var(--amber)"]]);
  });

  test("test_a_chip_in_hand_is_lit_and_nothing_of_it_moves_or_changes_size", () => {
    const inHand = STYLES.filter((rule) => /:(hover|focus-visible|focus|active)\b/.test(rule.selector));

    expect(inHand.map((rule) => rule.selector).sort()).toEqual([
      '.label[data-state="assumed"][data-ground="sand"] .opens:focus-visible',
      '.label[data-state="assumed"][data-ground="sand"] .opens:hover',
      ".off:focus-visible",
      ".off:hover",
      ".opens:focus-visible",
      ".opens:hover",
    ]);
    expect([...new Set(inHand.flatMap((rule) => [...rule.sets.keys()]))]).toEqual(["background-color"]);
    // Every word of a chip is ink, which is read on page, on sand and on amber alike.
    expect(STYLES.filter((rule) => rule.sets.has("color")).map((rule) => [rule.selector, rule.sets.get("color")])).toEqual([
      [".label", "var(--ink)"],
      [".holds", "inherit"],
    ]);
  });

  test("test_a_chip_keeps_two_art_pixels_over_and_under_its_words_unless_what_holds_it_says_less", () => {
    // Measured on a phone, with every part dressed: four rows of chips were 208 px, and the
    // first result ended under the foot of the first screen. A row that must be low says
    // how much room a chip keeps over and under its words. Where none says, it is as it was.
    const room = "var(--label-room, calc(var(--px) * 2))";

    expect(setsOf(".holds").get("padding")).toBe(`${room} calc(var(--px) * 4) ${room} calc(var(--px) * 3)`);
    // The kit itself never says less: only what lays a chip out may.
    expect(ALL.filter((rule) => rule.sets.has("--label-room")).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_the_shadow_of_a_chip_is_the_shadow_of_the_look_and_its_room_is_inside_the_box_of_the_chip", () => {
    const thrower = setsOf(".label::before");

    expect(setsOf(".label").get("padding")).toBe("0 calc(var(--px) * 2) calc(var(--px) * 2) 0");
    expect([thrower.get("position"), thrower.get("inset"), thrower.get("box-shadow")]).toEqual([
      "absolute",
      "0 calc(var(--px) * 2) calc(var(--px) * 2) 0",
      "var(--box-shadow)",
    ]);
    // No other rule throws a shadow of its own.
    expect(STYLES.filter((rule) => rule.sets.has("box-shadow")).map((rule) => rule.selector)).toEqual([".label::before"]);
  });

  test("test_a_chip_that_arrives_says_so_and_one_that_was_there_does_not", () => {
    const { container, rerender } = render(<Label thing={leafy} says="Leafy: more" />);
    expect(container.firstElementChild).toHaveAttribute("data-arrives", "false");

    rerender(<Label thing={leafy} says="Leafy: more" arrives />);
    expect(container.firstElementChild).toHaveAttribute("data-arrives", "true");
  });

  test("test_a_chip_that_arrives_drops_into_its_place_in_four_steps_and_settles_once", () => {
    const moving = ALL.filter(
      (rule) => [...rule.sets.keys()].some((property) => /^(animation|transition)/.test(property)) && rule.sets.get("animation") !== "none",
    );

    // The chip drops, and the shadow with it. The box of the chip holds still and cuts them off.
    expect(moving.map((rule) => [rule.selector, rule.sets.get("animation")])).toEqual([
      ['.label[data-arrives="true"]', "label-holds var(--motion-drop) step-end 1"],
      ['.label[data-arrives="true"] .chip', "label-drops var(--motion-drop) step-end 1"],
      ['.label[data-arrives="true"]::before', "label-drops var(--motion-drop) step-end 1"],
    ]);
    // Four steps, each held: out of sight above its box, half in, one step past, and settled.
    expect(framesOf("label-drops")).toEqual([
      ["0%", "transform: translateY(calc(-100% - var(--px) * 2));"],
      ["25%", "transform: translateY(-50%);"],
      ["50%", "transform: translateY(calc(var(--px) * 2));"],
      ["75%, 100%", "transform: translateY(0);"],
    ]);
    // Seen in a browser, in a picture taken at the first step: a strip of shadow stood at the
    // top of the box of every chip that arrived, with no chip over it, 4 px high on a phone
    // and 6 on a desk. What throws the shadow went up by its own height, and its shadow
    // falls two art pixels under it. So at the first step both go up by as much more as the
    // shadow falls, which is what the shadow of the look says.
    const falls = /^calc\(var\(--px\) \* (\d+)\) calc\(var\(--px\) \* (\d+)\)/.exec(asWritten()["--box-shadow"] ?? "");
    expect(falls?.[2]).toBe("2");
    expect(setsOf(".label::before").get("box-shadow")).toBe("var(--box-shadow)");
  });

  test("test_a_chip_that_arrives_moves_inside_its_own_box_which_is_there_before_it_arrives", () => {
    // While it drops it is cut off at the edge of its own box, so nothing of it is drawn outside.
    expect(framesOf("label-holds")).toEqual([["from, to", "clip-path: inset(0);"]]);
    // One step past is as far as its shadow falls, which is room the box has from the start.
    expect(setsOf(".label").get("padding")).toBe("0 calc(var(--px) * 2) calc(var(--px) * 2) 0");
    // That it arrives changes nothing of the room it takes: all that is said of it is that it moves.
    const arriving = STYLES.filter((rule) => /\[data-arrives/.test(rule.selector));
    expect([...new Set(arriving.flatMap((rule) => [...rule.sets.keys()]))]).toEqual(["animation"]);
    // Nothing is faded in: what is not yet in its box is cut off, and what is in it is whole.
    expect(/opacity|visibility/.test(CSS)).toBe(false);
  });

  test("test_for_a_person_who_asked_for_less_movement_a_chip_that_arrives_is_there", () => {
    // A browser that is told to end every movement at once still gives each its first
    // moment, in which the chip would be out of sight. So its movements are taken away.
    const stilled = ALL.filter((rule) => /prefers-reduced-motion:\s*reduce/.test(rule.under ?? ""));

    expect(stilled.map((rule) => [rule.selector, [...rule.sets]])).toEqual([
      ['.label[data-arrives="true"]', [["animation", "none"]]],
      ['.label[data-arrives="true"] .chip', [["animation", "none"]]],
      ['.label[data-arrives="true"]::before', [["animation", "none"]]],
    ]);
  });

  test("test_its_words_wrap_and_none_is_cut", () => {
    const cut = STYLES.filter(
      (rule) =>
        /hidden|clip/.test(rule.sets.get("overflow") ?? "") ||
        rule.sets.has("text-overflow") ||
        rule.sets.get("white-space") === "nowrap" ||
        rule.sets.has("height") ||
        rule.sets.has("max-height"),
    );

    // The cross is a drawing of one size, and holds no word.
    expect(cut.map((rule) => rule.selector)).toEqual([".cross"]);
    expect(setsOf(".label").get("max-width")).toBe("100%");
    expect(setsOf(".says").get("overflow-wrap")).toBe("anywhere");
  });

  test("test_what_a_chip_holds_is_read_and_is_set_in_the_reading_face", () => {
    expect(setsOf(".says").get("font-family")).toBe("var(--font-say)");
    expect(setsOf(".state").get("font-family")).toBe("var(--font-say)");
    expect(/var\(--font-name\)/.test(CSS)).toBe(false);
  });

  test("test_it_has_no_accessibility_fault", async () => {
    const { container } = render(
      <ul>
        {THING_STATES.map((state) => (
          <li key={state}>
            <Label
              thing={leafy}
              says="Leafy: more"
              named={`Leafy, ${state}`}
              state={state}
              onOpen={() => undefined}
              open={false}
              onTakeOff={() => undefined}
            />
          </li>
        ))}
        <li>
          <Label thing={{ kind: "usual" }} says="Usual settings: 7" state="assumed" arrives />
        </li>
      </ul>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});
