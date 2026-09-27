import { readFileSync } from "node:fs";
import path from "node:path";

import { act, fireEvent, render, screen } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { Fold } from "./Fold";
import { onTheGrass } from "./grass";
import { OpenToAddress } from "./OpenToAddress";

const SHEET = rulesOf(readFileSync(path.resolve(__dirname, "Fold.module.css"), "utf8"));
/** The sheet that draws every bar that folds, and so the bar of a fold of a page that explains. */
const OF_THE_BAR = rulesOf(readFileSync(path.resolve(__dirname, "..", "Disclosure", "Disclosure.module.css"), "utf8"));
const BARS = OF_THE_BAR.filter((rule) => !/forced-colors/.test(rule.under ?? ""));

const fold = () => document.querySelector("details") as HTMLDetailsElement;
const opens = () => fold().querySelector(":scope > summary") as HTMLElement;

describe("a fold of a page that explains", () => {
  test("test_it_is_the_browsers_own_and_is_closed_until_it_is_pressed_so_that_it_opens_with_scripts_off", () => {
    const markup = renderToStaticMarkup(
      <Fold says="How Burro works this out">
        <p>What goes into it.</p>
      </Fold>,
    );

    expect(markup).toMatch(/^<details[ >]/);
    expect(markup).not.toMatch(/<details[^>]* open/);
    expect(markup).not.toMatch(/<button|aria-expanded|onclick/i);
    // What it holds is in the page, closed, and is lost to nobody.
    expect(markup).toContain("What goes into it.");
  });

  test("test_it_says_what_a_person_would_ask_and_to_whoever_hears_the_page_what_it_is_asked_of", () => {
    render(
      <Fold says="How Burro works this out" of="Leafy">
        <p>What goes into it.</p>
      </Fold>,
    );

    // Many folds of one page say the same: each says what it is of, to whoever cannot see what it stands under.
    expect(opens().textContent).toBe("How Burro works this out: Leafy");
    const kept = opens().querySelector(".visually-hidden");
    expect(kept?.textContent).toBe(": Leafy");
    // Its arrow is dress and says nothing: nothing else of the bar is kept from whoever hears the page.
    const dress = [...opens().querySelectorAll("[aria-hidden]")];
    expect(dress).toHaveLength(1);
    expect(dress[0]).toBeEmptyDOMElement();
  });

  test("test_what_opens_it_takes_the_size_of_a_main_control_and_a_small_one_the_size_of_a_small_one", () => {
    const { unmount } = render(<Fold says="The full detail">words</Fold>);
    expect(opens()).toHaveClass("target");
    unmount();

    render(
      <Fold says="Every area" kind="line">
        words
      </Fold>,
    );
    expect(opens()).toHaveClass("target-min");
    expect(opens()).not.toHaveClass("target");
  });

  test("test_it_says_which_kind_it_is_and_may_be_led_to_by_its_id", () => {
    render(
      <Fold says="The full detail" kind="ground" id="detail">
        <section data-kind="box">What it holds.</section>
      </Fold>,
    );

    expect(fold()).toHaveAttribute("id", "detail");
    expect(fold()).toHaveAttribute("data-fold", "ground");
  });

  test("test_a_fold_that_stands_on_the_grass_is_read_on_cream_and_what_it_opens_brings_its_own_boxes", () => {
    const { container } = render(
      <Fold says="The full detail" kind="ground">
        <section data-kind="box">What it holds.</section>
      </Fold>,
    );

    // Its bar is a box of the kit. What it opens is given no ground: it stands boxes of its own on the grass.
    expect(opens()).toHaveAttribute("data-kind", "box");
    expect(opens().nextElementSibling).not.toHaveAttribute("data-kind");
    expect(onTheGrass(container)).toEqual([]);
  });

  test.each([
    ["bar", ["button", "bar", "alone", "target"]],
    ["ground", ["button", "bar", "boxed", "target"]],
  ] as const)("test_its_bar_is_the_bar_of_every_fold_of_the_website_with_its_arrow_in_a_cell_at_its_far_end: %s", (kind, classes) => {
    // Walked: the folds of the vibes, the methods and the sources stood on sand with the
    // arrow at the right and no cell, where the bars of the settings stand on cream with
    // the arrow in a cell. The founder asked for one thing, and a fold draws none of its own.
    render(
      <Fold says="The full detail" kind={kind}>
        words
      </Fold>,
    );

    expect(opens()).toHaveClass(...classes);
    expect(opens()).toHaveAttribute("data-arrow", "end");
    // The arrow comes first in the bar and is laid out last, in its cell: it says nothing, wherever it stands.
    expect([...opens().children].map((part) => [part.tagName, part.className])).toEqual([
      ["SPAN", "mark"],
      ["SPAN", "told"],
    ]);
    expect(opens().querySelector(".told")?.textContent).toBe("The full detail");
    // It is told from a bar that is open by the fold it stands in, which says so by itself.
    expect(fold()).toHaveClass("fold");
    expect(BARS.filter((rule) => rule.selector === ".fold[open] > .bar").map((rule) => rule.sets.get("background-color"))).toEqual([
      "var(--chosen)",
    ]);
  });

  test("test_a_small_fold_is_no_bar_and_has_its_mark_before_its_words_as_every_small_fold_has", () => {
    render(
      <Fold says="Every area" of="Leafy" kind="line">
        words
      </Fold>,
    );

    expect(opens()).toHaveClass("button", "small", "target-min");
    expect(opens()).not.toHaveClass("bar");
    expect(opens()).not.toHaveAttribute("data-arrow");
    const said = opens().firstElementChild as HTMLElement;
    expect(said.firstElementChild).toHaveAttribute("aria-hidden", "true");
    expect(said.textContent).toBe("Every area: Leafy");
  });

  test("test_the_arrow_is_handed_to_the_style_sheet_by_name_once_for_the_fold", () => {
    render(<Fold says="The full detail">words</Fold>);

    expect(fold().style.getPropertyValue("--arrow")).toBe('url("/art/ui-arrow.png")');
    expect([fold().style.getPropertyValue("--arrow-w"), fold().style.getPropertyValue("--arrow-h")]).toEqual(["10", "8"]);
    // Its bar has it from the fold, and bears no style of its own.
    expect(opens()).not.toHaveAttribute("style");
  });

  test("test_the_arrow_points_down_at_what_is_closed_and_up_once_it_is_open_and_turns_at_once", () => {
    // The drawing points up. It is turned for a fold that is closed, in one step and not over time.
    const of = (selector: string) => new Map(BARS.filter((rule) => rule.selector === selector).flatMap((rule) => [...rule.sets]));
    expect(of(".bar .mark::before").get("transform")).toBe("rotate(180deg)");
    expect(of(".fold[open] > .bar .mark::before").get("transform")).toBe("none");
    expect([...SHEET, ...BARS].filter((rule) => [...rule.sets.keys()].some((property) => /^(transition|animation)/.test(property)))).toEqual([]);
  });

  test("test_the_fold_draws_nothing_of_its_bar_and_says_only_where_what_it_opens_stands", () => {
    // What a bar stands on, its edge, its arrow and what it is in hand are said once, by the
    // sheet that draws every bar: a fold that said its own was drawn its own way.
    const ofABar = SHEET.filter((rule) => /summary|::before|::after|:hover|:focus|:active/.test(rule.selector));
    const drawn = SHEET.flatMap((rule) =>
      [...rule.sets.keys()].filter((property) => /^(background|color|border|box-shadow|font|transform|outline)/.test(property)).map((property) => `${rule.selector} sets ${property}`),
    );

    expect([...new Set(SHEET.map((rule) => rule.selector))]).toEqual([
      ".fold",
      '.fold[data-fold="bar"] > .opened',
      '.fold[data-fold="line"] > .opened',
      '.fold[data-fold="ground"]',
      '.fold[data-fold="ground"] > .opened',
    ]);
    expect(ofABar.map((rule) => rule.selector)).toEqual([]);
    expect(drawn).toEqual([]);
  });

  test("test_what_the_bar_of_a_fold_on_the_grass_says_begins_where_the_words_of_the_boxes_it_opens_begin", () => {
    // As far in as a box of the page keeps what it holds, at every width: the page knows its own rooms.
    const begins = SHEET.filter((rule) => rule.sets.has("--bar-begins")).map((rule) => [rule.selector, rule.under, rule.sets.get("--bar-begins")]);

    expect(begins).toEqual([
      ['.fold[data-fold="ground"]', null, "var(--space-3)"],
      ['.fold[data-fold="ground"]', "@media (min-width: 40rem)", "var(--space-4)"],
      ['.fold[data-fold="ground"]', "@media (min-width: 60rem)", "var(--space-5)"],
    ]);
    // The fold says where a bar begins with no weight, so that what is said here is what holds.
    expect(OF_THE_BAR.filter((rule) => rule.sets.has("--bar-begins")).map((rule) => rule.selector)).toEqual([":where(.disclosure)", ":where(.fold)"]);
    expect(BARS.filter((rule) => rule.selector === ".boxed > .told").map((rule) => rule.sets.get("padding-inline"))).toEqual([
      "var(--bar-begins) calc(var(--px) * 4)",
    ]);
  });

  test("test_no_edge_of_a_fold_is_dashed_and_every_colour_is_a_token", () => {
    const written = readFileSync(path.resolve(__dirname, "Fold.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");

    expect(/dashed|dotted/.test(written)).toBe(false);
    expect(written.match(/#[0-9a-f]{3,8}\b|\b(rgb|hsl)a?\(/gi) ?? []).toEqual([]);
  });

  test("test_it_has_no_accessibility_fault", async () => {
    const { container } = render(
      <main>
        <h1>Methods</h1>
        <Fold says="The full detail" kind="ground">
          <section data-kind="box" aria-label="A part">
            <h2>A part</h2>
            <Fold says="Every area" of="Leafy" kind="line">
              <p>Every area.</p>
            </Fold>
          </section>
        </Fold>
      </main>,
    );

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});

describe("a fold of a page that explains, under the press", () => {
  test("test_its_bar_is_where_it_was_after_it_is_pressed_as_the_bar_of_every_fold_is", () => {
    // Walked by keyboard at 1440 by 900: on the page of vibes the bar of Leafy stood at 352
    // and after Enter stood at 303, with the page not scrolled. What holds a bar still is
    // the fold's, and its own test holds how: here, that a fold of these pages is one.
    const asked: FrameRequestCallback[] = [];
    const moved: number[] = [];
    let stands = 352;
    jest.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => asked.push(callback));
    jest.spyOn(window, "scrollBy").mockImplementation(((_: number, by: number) => {
      moved.push(by);
    }) as typeof window.scrollBy);
    jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (this: HTMLElement) {
      const top = this.tagName === "SUMMARY" ? stands : 0;
      return { top, bottom: top + 44, left: 0, right: 0, x: 0, y: top, width: 0, height: 44, toJSON: () => ({}) };
    });
    render(
      <Fold says="How Burro works this out" of="Leafy">
        words
      </Fold>,
    );

    fireEvent.click(opens());
    stands = 303;
    act(() => asked.forEach((one) => one(0)));

    expect(moved).toEqual([303 - 352]);
    jest.restoreAllMocks();
  });
});

describe("a page that is opened at a part of itself", () => {
  const page = () =>
    render(
      <>
        <OpenToAddress />
        <Fold says="The full detail" kind="ground">
          <h2 id="journeys">How journeys are timed</h2>
          <Fold says="Every area" kind="line">
            <p id="every">Every area.</p>
          </Fold>
        </Fold>
        <Fold says="Another" id="another">
          <p>Another part.</p>
          <h2 id="words" tabIndex={-1}>
            How your words are handled
          </h2>
        </Fold>
      </>,
    );
  const folds = () => [...document.querySelectorAll("details")].map((one) => one.open);
  const seen: string[] = [];

  beforeEach(() => {
    seen.length = 0;
    Element.prototype.scrollIntoView = function scrollIntoView(this: Element) {
      seen.push(this.id);
    };
  });

  afterEach(() => {
    window.location.hash = "";
  });

  test("test_every_fold_that_holds_what_the_address_names_is_opened_and_it_is_brought_into_sight", () => {
    // Another page leads here by the id of a part, which now stands in a fold.
    window.location.hash = "#journeys";
    page();

    expect(folds()).toEqual([true, false, false]);
    expect(seen).toEqual(["journeys"]);
  });

  test("test_a_fold_inside_a_fold_is_opened_with_the_fold_that_holds_it", () => {
    window.location.hash = "#every";
    page();

    expect(folds()).toEqual([true, true, false]);
  });

  test("test_a_fold_that_the_address_names_is_opened_itself", () => {
    window.location.hash = "#another";
    page();

    expect(folds()).toEqual([false, false, true]);
  });

  test("test_with_no_part_named_or_one_that_is_not_there_nothing_is_opened_and_nothing_is_moved", () => {
    page();
    expect(folds()).toEqual([false, false, false]);
    act(() => {
      window.location.hash = "#no-such-part";
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    });

    expect(folds()).toEqual([false, false, false]);
    expect(seen).toEqual([]);
  });

  test("test_a_link_of_the_page_itself_opens_the_fold_it_leads_into", () => {
    page();
    act(() => {
      window.location.hash = "#journeys";
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    });

    expect(folds()).toEqual([true, false, false]);
    expect(seen).toEqual(["journeys"]);
  });

  test("test_a_link_of_the_page_itself_that_the_framework_follows_opens_the_fold_though_no_change_of_address_is_told", () => {
    // Seen in a browser, at both sizes: from the page of methods, the link of the foot to a
    // part of the methods changed the address and opened nothing, and the part stayed in its
    // fold. The framework follows a link of its own by writing the address itself, and the
    // browser then tells nobody that the address changed.
    page();
    const link = document.createElement("a");
    link.href = `${window.location.pathname}#journeys`;
    link.textContent = "How journeys are timed";
    link.addEventListener("click", (event) => {
      event.preventDefault();
      window.history.pushState(null, "", "#journeys");
    });
    document.body.append(link);

    try {
      fireEvent.click(link);

      expect(window.location.hash).toBe("#journeys");
      expect(folds()).toEqual([true, false, false]);
      expect(seen).toEqual(["journeys"]);
    } finally {
      link.remove();
    }
  });

  test("test_a_part_that_can_take_the_focus_takes_it_as_it_is_opened_and_one_that_cannot_is_left_as_it_is", () => {
    // Seen in a browser: the part was brought into sight and the focus was left on the link
    // at the foot of the page, so that whoever hears the page was left at the foot.
    window.location.hash = "#words";
    page();

    expect(folds()).toEqual([false, false, true]);
    expect(seen).toEqual(["words"]);
    expect(document.getElementById("words")).toHaveFocus();
    // A part that was not made to take the focus is given nothing so that it may.
    act(() => {
      window.location.hash = "#journeys";
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    });
    expect(document.getElementById("journeys")?.hasAttribute("tabindex")).toBe(false);
    expect(document.getElementById("journeys")).not.toHaveFocus();
  });

  test("test_a_part_that_stands_open_takes_the_focus_when_a_link_of_the_framework_leads_to_it_again", () => {
    window.location.hash = "#words";
    page();
    const link = document.createElement("a");
    link.href = `${window.location.pathname}#words`;
    link.addEventListener("click", (event) => event.preventDefault());
    document.body.append(link);

    try {
      link.focus();
      seen.length = 0;
      fireEvent.click(link);

      // Nothing was closed, so nothing is brought anywhere: the framework does that. The focus goes to the part.
      expect(seen).toEqual([]);
      expect(document.getElementById("words")).toHaveFocus();
    } finally {
      link.remove();
    }
  });

  test("test_a_link_that_leads_to_another_page_or_is_opened_elsewhere_opens_nothing_here", () => {
    page();
    const made = (href: string) => {
      const link = document.createElement("a");
      link.href = href;
      link.addEventListener("click", (event) => event.preventDefault());
      document.body.append(link);
      return link;
    };
    const [elsewhere, here, nowhere] = [made("/another-page#journeys"), made(`${window.location.pathname}#journeys`), made(`${window.location.pathname}#no-such-part`)];

    try {
      fireEvent.click(elsewhere);
      fireEvent.click(nowhere);
      // Pressed with a key that opens it in a tab of its own, it leads this page nowhere.
      fireEvent.click(here, { metaKey: true });
      fireEvent.click(here, { ctrlKey: true });
      fireEvent.click(here, { button: 1 });

      expect(folds()).toEqual([false, false, false]);
      expect(seen).toEqual([]);
    } finally {
      for (const link of [elsewhere, here, nowhere]) link.remove();
    }
  });

  test("test_once_the_page_is_gone_a_press_opens_nothing_of_it", () => {
    const { unmount } = page();
    const link = document.createElement("a");
    link.href = `${window.location.pathname}#journeys`;
    link.addEventListener("click", (event) => event.preventDefault());
    document.body.append(link);
    unmount();

    try {
      fireEvent.click(link);
      expect(seen).toEqual([]);
    } finally {
      link.remove();
    }
  });

  test("test_it_draws_nothing_and_keeps_nothing", () => {
    const { container } = render(<OpenToAddress />);

    expect(container).toBeEmptyDOMElement();
    expect(screen.queryByRole("button")).toBeNull();
  });
});
