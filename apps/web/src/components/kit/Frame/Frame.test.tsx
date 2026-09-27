import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";

import { faultsIn } from "../../../../test/support/axe";
import { asWritten, writtenForAWideScreen } from "../../../../test/support/contrast";
import { rulesOf, weightOf } from "../../../../test/support/css";
import { cutOf, isDrawn } from "../drawings";
import { Frame, FRAME_KINDS } from "./Frame";

const CSS = readFileSync(path.join(__dirname, "Frame.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const ALL = rulesOf(CSS);
const STYLES = ALL.filter((rule) => rule.under === null);
const FORCED = ALL.filter((rule) => /forced-colors/.test(rule.under ?? ""));
/** What the style sheet sets of a selector, in all: one may be named by more rules than one. */
const setsOf = (selector: string, rules = STYLES) =>
  new Map(rules.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));

/** The tokens as a phone has them, and as a wide screen has them. */
const NARROW = asWritten();
const WIDE = { ...NARROW, ...writtenForAWideScreen() };
/** Four lengths, as a token writes them, each as a count of art pixels. */
const inArtPixels = (written: string | undefined) =>
  (written ?? "").match(/calc\(var\(--px\) \* \d+\)|\b0\b/g)?.map((part) => Number(/\* (\d+)/.exec(part)?.[1] ?? 0)) ?? [];

describe("a box", () => {
  test("test_a_frame_is_the_element_it_is_told_to_be_and_a_div_where_it_is_told_nothing", () => {
    const { container } = render(
      <>
        <Frame kind="plain">A row</Frame>
        <Frame kind="box" as="section" aria-label="What Burro understood">
          A box
        </Frame>
        <Frame kind="box-on" as="p">
          The one in hand
        </Frame>
      </>,
    );

    expect(container.children[0]?.tagName).toBe("DIV");
    expect(screen.getByRole("region", { name: "What Burro understood" })).toHaveTextContent("A box");
    expect(screen.getByText("The one in hand").tagName).toBe("P");
  });

  test("test_a_frame_says_nothing_of_itself_to_a_screen_reader_and_holds_what_it_is_given", () => {
    render(
      <Frame kind="plain" as="ul">
        <li>Cindermoor</li>
        <li>Farrowmere</li>
      </Frame>,
    );

    // It is a list of two, as it would be with no frame round it.
    expect(screen.getByRole("list")).not.toHaveAttribute("aria-label");
    expect(screen.getAllByRole("listitem").map((item) => item.textContent)).toEqual(["Cindermoor", "Farrowmere"]);
  });

  test("test_whatever_lays_a_frame_out_may_say_where_it_stands", () => {
    const { container } = render(
      <Frame kind="box" className="beside-the-map" id="first">
        A box
      </Frame>,
    );

    expect(container.firstElementChild).toHaveClass("beside-the-map", "frame", "box");
    expect(container.firstElementChild).toHaveAttribute("id", "first");
  });

  test("test_a_page_may_give_the_focus_to_a_frame_it_has_made_able_to_take_it", () => {
    const found: { current: HTMLElement | null } = { current: null };
    render(
      <Frame kind="box" as="section" ref={found} tabIndex={-1} aria-label="What Burro understood">
        A box
      </Frame>,
    );

    found.current?.focus();
    expect(screen.getByRole("region", { name: "What Burro understood" })).toHaveFocus();
  });

  test.each(FRAME_KINDS)("test_a_frame_says_which_kind_it_is_and_is_drawn_as_that_kind_alone: %s", (kind) => {
    const { container } = render(<Frame kind={kind}>What it holds</Frame>);
    const frame = container.firstElementChild as HTMLElement;

    expect(frame).toHaveAttribute("data-kind", kind);
    expect(FRAME_KINDS.filter((one) => frame.classList.contains(one))).toEqual([kind]);
  });

  test("test_a_frame_keeps_what_it_holds_clear_of_its_edge_unless_it_is_told_that_it_brings_its_own_room", () => {
    const { container } = render(
      <>
        <Frame kind="box">A sentence</Frame>
        <Frame kind="box" bare>
          <table />
        </Frame>
      </>,
    );

    expect(container.children[0]).toHaveClass("roomy");
    expect(container.children[1]).not.toHaveClass("roomy");
    // The room is a class of its own, so that a frame without it is given none here: whatever
    // lays a bare frame out may give it any, and is not held against a rule of this sheet.
    expect(STYLES.filter((rule) => rule.sets.has("padding")).map((rule) => rule.selector)).toEqual([".roomy"]);
  });

  test("test_the_picture_of_a_box_is_named_by_a_token_and_is_laid_as_the_tokens_say", () => {
    for (const selector of [".box::before", ".box-on::before"]) {
      expect([selector, setsOf(selector).get("border-image")]).toEqual([
        selector,
        "var(--frame-box) var(--frame-box-cut) fill / var(--frame-box-wide) / var(--frame-box-out) repeat",
      ]);
      expect([selector, setsOf(selector).get("image-rendering")]).toEqual([selector, "pixelated"]);
    }
    // A box that is chosen, or in hand, has the picture of one: the same, cut and laid the same way.
    expect(setsOf(".box-on::before").get("border-image-source")).toBe("var(--frame-box-on)");
    expect(setsOf(".box::before").has("border-image-source")).toBe(false);
    // Its sides are laid end to end. Stretched, or made to fit, a pixel of it would be no square.
    const laid = ALL.flatMap((rule) => [...rule.sets].filter(([property]) => property.startsWith("border-image")).map(([, value]) => value));
    expect(laid.filter((value) => /\b(stretch|round|space)\b/.test(value))).toEqual([]);
    // No style sheet names the picture itself, so that one line of the tokens turns it off.
    expect(/url\(/.test(CSS)).toBe(false);
  });

  test("test_the_picture_of_a_box_in_hand_is_asked_for_with_the_page_and_not_at_the_first_press_in_it", () => {
    // Seen in a browser, on a phone: the picture of a box in hand was asked for at the first
    // press in the box of the search, and until it had come the box was drawn with no edge
    // at all. On a slow line that lasts as long as the picture takes. So every box lays that
    // picture as a ground of no size, which is asked for with the page and never seen.
    for (const selector of [".box::before", ".box-on::before"]) {
      const sets = setsOf(selector);
      expect([selector, sets.get("background-image"), sets.get("background-size"), sets.get("background-repeat")]).toEqual([
        selector,
        "var(--frame-box-on)",
        "0 0",
        "no-repeat",
      ]);
      // What is seen of the ground of a box is its colour, as it was, laid inside its edge.
      expect([selector, sets.get("background-color"), sets.get("background-clip")]).toEqual([selector, "var(--page)", "padding-box"]);
    }
    // No rule lays the picture at a size, and none names another.
    const laid = ALL.filter((rule) => rule.sets.has("background-size") || rule.sets.has("background-image"));
    expect(laid.map((rule) => [rule.under, rule.selector, rule.sets.get("background-size")])).toEqual([
      [null, ".box::before", "0 0"],
      [null, ".box-on::before", "0 0"],
    ]);
    expect(isDrawn("frame-box-on")).toBe(true);
    expect(NARROW["--frame-box-on"]).toBe('url("/art/frame-box-on.png")');
  });

  test("test_with_no_picture_and_no_shadow_a_box_is_a_plain_ink_edge_and_holds_what_it_held", () => {
    // To turn the look down, a person sets `--frame-box` and `--box-shadow` to `none`.
    const LOOK = /var\(--(frame-box|frame-box-on|box-shadow)\)/;
    /** What sets the room a thing takes, or where it lies. */
    const ROOM = /^(width|height|min-.*|max-.*|padding.*|margin.*|border-width|border-style|inset.*|top|right|bottom|left|display|position)$/;

    for (const selector of [".box::before", ".box-on::before"]) {
      const sets = setsOf(selector);
      // Under the picture is an edge of ink, one art pixel wide, and inside it the page.
      expect([selector, sets.get("border")]).toEqual([selector, "var(--edge) solid var(--border)"]);
      expect([selector, sets.get("background-color"), sets.get("background-clip")]).toEqual([
        selector,
        "var(--page)",
        "padding-box",
      ]);
      // The picture and the shadow are each named once, whole, where a `none` takes them away.
      expect([selector, sets.get("box-shadow")]).toEqual([selector, "var(--box-shadow)"]);
      // The picture of a box in hand is named once more, as a ground of no size: a `none` takes that away too.
      expect([selector, [...sets].filter(([, value]) => LOOK.test(value)).map(([property]) => property).sort()]).toEqual([
        selector,
        selector === ".box-on::before"
          ? ["background-image", "border-image", "border-image-source", "box-shadow"]
          : ["background-image", "border-image", "box-shadow"],
      ]);
    }
    // Nothing that gives a box its room names the picture or the shadow: so with both gone
    // the box is as large as it was, and what it holds stands where it stood.
    const rooms = ALL.flatMap((rule) => [...rule.sets].filter(([property]) => ROOM.test(property)).map(([property, value]) => ({ rule, property, value })));
    expect(rooms.length).toBeGreaterThan(5);
    expect(rooms.filter(({ value }) => LOOK.test(value)).map(({ rule, property }) => `${rule.selector} sets ${property}`)).toEqual([]);
    // What a box holds is in the box itself, and never in the layer that is drawn behind it.
    const { container } = render(
      <Frame kind="box">
        <p>What it holds</p>
      </Frame>,
    );
    expect(container.firstElementChild?.children).toHaveLength(1);
    expect(setsOf(".box::before").get("content")).toBe('""');
    expect(setsOf(".box::before").get("pointer-events")).toBe("none");
  });

  test("test_the_shadow_of_a_box_falls_inside_the_room_the_box_takes_so_that_no_page_is_made_wider", () => {
    // Seen in a browser: a shadow that falls outside its box is cut off at the edge of a
    // phone's screen, or makes the page wider than its window. So the room of the shadow is
    // the box's own: its edge is as wide as the picture is drawn, the shadow in it.
    for (const kind of [".box", ".box-on"]) {
      expect([kind, setsOf(kind).get("border-width"), setsOf(kind).get("border-color")]).toEqual([
        kind,
        "var(--frame-box-wide)",
        "transparent",
      ]);
      // What is drawn lies inside the frame, against the frame, and takes no press.
      expect([kind, setsOf(`${kind}::before`).get("position"), setsOf(`${kind}::before`).get("z-index")]).toEqual([
        kind,
        "absolute",
        "-1",
      ]);
      expect([kind, setsOf(`${kind}::before`).get("inset")]).toEqual([kind, "calc(var(--px) * -4)"]);
    }
    expect([setsOf(".frame").get("position"), setsOf(".frame").get("isolation")]).toEqual(["relative", "isolate"]);
    // No frame is pulled out past what holds it: no margin is less than nothing. A minus
    // stands before a figure, a bracket or a token there, and the name of a token holds two.
    const LESS_THAN_NOTHING = /(^|[\s(*,])-(?=[\d.]|var\(|calc\()/;
    expect(["-4px", "calc(var(--px) * -4)", "0 -1rem", "calc(-1 * var(--px))"].filter((value) => !LESS_THAN_NOTHING.test(value))).toEqual([]);
    expect(["calc(var(--px) * 2)", "var(--space-3)", "0 auto"].filter((value) => LESS_THAN_NOTHING.test(value))).toEqual([]);
    expect(
      ALL.filter((rule) => [...rule.sets].some(([property, value]) => property.startsWith("margin") && LESS_THAN_NOTHING.test(value))),
    ).toEqual([]);

    // The tokens say how wide the picture is drawn and how far its shadow stands out. What is
    // left is the rule, which is as wide as the layer is set out: and the shadow stands out
    // as far as the shadow of the look falls, on a phone and on a wide screen.
    const wide = inArtPixels(NARROW["--frame-box-wide"]);
    const out = inArtPixels(NARROW["--frame-box-out"]);
    expect([wide.length, out.length]).toEqual([4, 4]);
    expect(wide.map((width, at) => width - (out[at] ?? 0))).toEqual([4, 4, 4, 4]);
    for (const tokens of [NARROW, WIDE]) {
      const [right, down] = (tokens["--box-shadow"] ?? "").split(/\s+(?![^(]*\))/);
      expect([inArtPixels(right), inArtPixels(down)]).toEqual([[out[1]], [out[2]]]);
    }
  });

  test("test_a_box_is_cut_in_nine_where_its_drawing_says", () => {
    const named = (token: string) => /^url\("\/art\/([a-z0-9-]+)\.png"\)$/.exec(NARROW[token] ?? "")?.[1] ?? "";
    const cut = (NARROW["--frame-box-cut"] ?? "").split(/\s+/).map(Number);

    for (const token of ["--frame-box", "--frame-box-on"]) {
      const name = named(token);
      expect([token, isDrawn(name)]).toEqual([token, true]);
      expect([token, isDrawn(name) ? cutOf(name) : null]).toEqual([token, cut]);
    }
  });

  test("test_a_plain_frame_is_an_ink_edge_and_nothing_else", () => {
    const sets = setsOf(".plain");

    expect(sets.get("border")).toBe("var(--edge) solid var(--border)");
    expect(sets.get("background")).toBe("var(--page)");
    // No second rule, no notch and no shadow: no picture, and no layer behind it.
    expect([sets.has("border-image"), sets.has("box-shadow")]).toEqual([false, false]);
    expect(STYLES.filter((rule) => /^\.plain::/.test(rule.selector))).toEqual([]);
  });

  test("test_a_plain_frame_that_stands_on_the_grass_ends_where_the_edge_of_ink_of_a_box_ends", () => {
    // Measured in a browser, at 1440 by 900: results six and on, which are plain frames,
    // ended at 1,032, where the edge of ink of the cards over them ended at 1,026. So did
    // what stands under a list of results, and the slip at the foot of the statement of
    // accessibility. A box keeps the room of its shadow inside itself, two art pixels at
    // its far side, and a plain frame kept none.
    const ON_THE_GRASS = ".plain:not(:where(.frame *))";
    const kept = STYLES.filter((rule) => [...rule.sets.keys()].some((property) => property.startsWith("margin")));

    expect(kept.map((rule) => [rule.selector, [...rule.sets]])).toEqual([
      [ON_THE_GRASS, [["margin-inline-end", "calc(var(--px) * 2)"]]],
    ]);
    // It is as far as the shadow of a box stands out at its far side, which the tokens say.
    expect(inArtPixels(NARROW["--frame-box-out"])[1]).toBe(2);
    // It weighs what a class weighs, and no more: whatever lays a plain frame out may say otherwise.
    expect(weightOf(ON_THE_GRASS)).toEqual([0, 1, 0]);

    // A frame that stands in a box, or in another frame, is as wide as what holds it: the
    // room is for one that stands on the grass, among boxes.
    const { container } = render(
      <div data-dressed="">
        {/* A result says of itself which kind it is, as a frame does, and is no frame. */}
        <ol>
          <li data-kind="row">
            <Frame kind="plain" id="on-the-grass">
              Results six and on
            </Frame>
          </li>
        </ol>
        <div>
          <Frame kind="plain" as="p" id="in-a-part-of-the-page">
            Last updated
          </Frame>
        </div>
        <Frame kind="box">
          <Frame kind="plain" id="in-a-box">
            A table
          </Frame>
        </Frame>
        <Frame kind="plain">
          <Frame kind="plain" id="in-a-frame">
            A row
          </Frame>
        </Frame>
        <Frame kind="box" id="a-box">
          A result
        </Frame>
      </div>,
    );
    expect([...container.querySelectorAll(ON_THE_GRASS)].map((frame) => frame.id).filter(Boolean)).toEqual([
      "on-the-grass",
      "in-a-part-of-the-page",
    ]);
  });

  test("test_with_forced_colours_no_picture_is_drawn_and_the_systems_colours_carry_the_edge", () => {
    for (const selector of [".box::before", ".box-on::before"]) {
      const forced = FORCED.filter((rule) => rule.selector === selector);
      // Said once of each, in one rule, where the picture is taken off.
      expect([selector, forced.map((rule) => rule.sets.get("border-image-source"))]).toEqual([selector, ["none"]]);
      expect([selector, forced.map((rule) => rule.sets.get("box-shadow"))]).toEqual([selector, ["none"]]);
    }
    // A picture is taken away by its source. Said as the whole of `border-image`, the build
    // makes nothing of it, and the picture is still there: seen in a browser.
    expect(ALL.filter((rule) => (rule.sets.get("border-image") ?? "").trim() === "none").map((rule) => rule.selector)).toEqual([]);
    // Seen in a browser that forces colours: every box had a band of ink at its right and
    // its foot, 6 px wide on a desk. A box keeps the room of its rule and of its shadow as
    // an edge of its own that is clear, and a browser that forces colours draws an edge that
    // is clear in the colour of words. So that edge is the colour of the ground there, which
    // is a colour of the system and is kept: the room stays, and nothing is drawn in it.
    for (const selector of [".box", ".box-on"]) {
      const forced = FORCED.filter((rule) => rule.selector === selector);
      expect([selector, forced.map((rule) => [...rule.sets])]).toEqual([selector, [[["border-color", "Canvas"]]]]);
    }
    // Nothing of a frame is taken out of the colours of the system, which what it holds would follow.
    expect(ALL.filter((rule) => rule.sets.has("forced-color-adjust")).map((rule) => rule.selector)).toEqual([]);
  });

  test("test_it_has_no_accessibility_fault", async () => {
    const { container } = render(
      <Frame kind="box" as="section" aria-label="A result">
        <Frame kind="box-on" as="p">
          The one in hand
        </Frame>
        <Frame kind="plain" as="ul" bare>
          <li>Cindermoor</li>
        </Frame>
      </Frame>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});
