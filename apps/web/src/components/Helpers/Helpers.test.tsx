import { readFileSync } from "node:fs";
import path from "node:path";

import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useRef, useState } from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { HEAD, type Opens } from "@/lib/sight";

import { faultsIn } from "../../../test/support/axe";
import { asWritten, writtenForAWideScreen } from "../../../test/support/contrast";
import { rulesOf } from "../../../test/support/css";
import { Helpers, useHelper, type Helper, type HelpersHandle } from "./Helpers";
import { laidOut, type Sizes } from "./laid";

const user = () => userEvent.setup({ delay: null });

type Id = "one" | "two" | "three";

const THREE: readonly Helper<Id>[] = [
  { id: "one", label: "The first", children: <button type="button">inside the first</button> },
  { id: "two", label: "The second", children: <p>inside the second</p> },
  { id: "three", label: "The third", children: <input type="text" aria-label="inside the third" /> },
];

/** The helpers as a page holds them: it keeps which one is open, and nothing else. */
function Held({
  helpers = THREE,
  heard,
  opens,
}: {
  readonly helpers?: readonly Helper<Id>[];
  readonly heard?: (id: Id | null) => void;
  readonly opens?: Opens;
}) {
  const [open, setOpen] = useState<Id | null>(null);
  return (
    <Helpers
      label="Ways in"
      helpers={helpers}
      open={open}
      opens={opens}
      onOpen={(id) => {
        heard?.(id);
        setOpen(id);
      }}
    />
  );
}

const line = () => screen.getByRole("group", { name: "Ways in" });
const helper = (name: string) => within(line()).getByRole("button", { name });
/** What a helper opens: the part of the page its button names. */
const openedBy = (name: string) => document.getElementById(helper(name).getAttribute("aria-controls") ?? "") as HTMLElement;
const comesBefore = (one: Element, other: Element) =>
  Boolean(one.compareDocumentPosition(other) & Node.DOCUMENT_POSITION_FOLLOWING);

describe("the helpers", () => {
  test("test_each_helper_is_a_native_button_that_says_it_is_closed_and_holds_nothing_until_it_is_pressed", () => {
    render(<Held />);

    const buttons = within(line()).getAllByRole("button");
    expect(buttons.map((button) => button.textContent)).toEqual(["The first", "The second", "The third"]);
    for (const button of buttons) {
      expect(button.tagName).toBe("BUTTON");
      expect(button).toHaveAttribute("type", "button");
      expect(button).toHaveAttribute("aria-expanded", "false");
      expect(button).toHaveClass("target");
      // The part it names is on the page, so that the name leads somewhere, and is empty.
      const part = document.getElementById(button.getAttribute("aria-controls") ?? "");
      expect(part).not.toBeNull();
      expect(part).not.toBeVisible();
      expect(part?.childNodes).toHaveLength(0);
    }
    expect(screen.queryByText("inside the second")).toBeNull();
  });

  test("test_what_a_helper_opens_stands_directly_under_the_line_and_moves_no_helper", async () => {
    render(<Held />);
    const before = within(line()).getAllByRole("button");

    await user().click(helper("The second"));

    expect(helper("The second")).toHaveAttribute("aria-expanded", "true");
    expect(openedBy("The second")).toHaveTextContent("inside the second");
    expect(openedBy("The second")).toBeVisible();
    // The line is the same line, with the same buttons in the same places: nothing was put among them.
    expect(within(line()).getAllByRole("button")).toEqual(before);
    expect(line().contains(openedBy("The second"))).toBe(false);
    expect(comesBefore(line(), openedBy("The second"))).toBe(true);
    // Nothing that is drawn stands between the line and what was opened.
    const between = [...(line().parentElement?.children ?? [])].filter(
      (part) => comesBefore(line(), part) && comesBefore(part, openedBy("The second")) && !part.hasAttribute("hidden"),
    );
    expect(between).toEqual([]);
  });

  test("test_one_helper_is_open_at_a_time", async () => {
    render(<Held />);
    const press = user();

    await press.click(helper("The first"));
    await press.click(helper("The third"));

    expect(within(line()).getAllByRole("button").map((button) => button.getAttribute("aria-expanded"))).toEqual([
      "false",
      "false",
      "true",
    ]);
    expect(screen.queryByRole("button", { name: "inside the first" })).toBeNull();
    expect(screen.getByRole("textbox", { name: "inside the third" })).toBeInTheDocument();
  });

  test("test_pressing_the_open_helper_closes_it_and_the_focus_stays_on_it", async () => {
    const heard = jest.fn();
    render(<Held heard={heard} />);
    const press = user();

    await press.click(helper("The first"));
    await press.click(helper("The first"));

    expect(heard.mock.calls).toEqual([["one"], [null]]);
    expect(helper("The first")).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("button", { name: "inside the first" })).toBeNull();
    expect(helper("The first")).toHaveFocus();
  });

  test("test_the_helper_that_is_pressed_has_the_focus_when_what_had_it_goes_with_the_one_it_closes", async () => {
    render(<Held />);
    const press = user();
    await press.click(helper("The first"));
    await press.click(screen.getByRole("button", { name: "inside the first" }));
    expect(screen.getByRole("button", { name: "inside the first" })).toHaveFocus();

    // A press as a browser makes it that gives no focus to a button: the focus is not
    // left in what the press takes away.
    fireEvent.click(helper("The second"));

    expect(screen.queryByRole("button", { name: "inside the first" })).toBeNull();
    expect(helper("The second")).toHaveFocus();
    expect(document.body).not.toHaveFocus();
  });

  test("test_the_helper_that_is_pressed_takes_the_focus_and_the_page_is_not_moved_under_the_press", () => {
    // Seen in a browser, with a press made as a browser makes it that gives no focus to a
    // button: the page was brought up for the helper that took the focus, by 345 px on a
    // phone 664 px high and by 250 px in a window 600 px high, under the finger that had
    // pressed it. What is pressed is in sight already, so nothing is brought into sight.
    render(<Held />);
    const asked = jest.spyOn(HTMLElement.prototype, "focus");

    fireEvent.click(helper("The second"));

    expect(helper("The second")).toHaveFocus();
    expect(asked.mock.contexts).toEqual([helper("The second")]);
    expect(asked.mock.calls).toEqual([[{ preventScroll: true }]]);
  });

  test("test_escape_brings_the_helper_into_sight_as_it_takes_the_focus_for_it_may_be_out_of_sight", async () => {
    // What a helper holds may be long, and Escape may be pressed at the foot of it, with the
    // helper over the top of the screen. The focus is never put on what is out of sight.
    render(<Held />);
    const press = user();
    await press.click(helper("The third"));
    await press.tab();
    const asked = jest.spyOn(HTMLElement.prototype, "focus");

    await press.keyboard("{Escape}");

    expect(helper("The third")).toHaveFocus();
    expect(asked.mock.contexts).toEqual([helper("The third")]);
    expect(asked.mock.calls).toEqual([[]]);
  });

  test("test_escape_closes_what_is_open_and_puts_the_focus_back_on_its_helper", async () => {
    render(<Held />);
    const press = user();
    await press.click(helper("The third"));
    await press.tab();
    expect(screen.getByRole("textbox", { name: "inside the third" })).toHaveFocus();

    await press.keyboard("{Escape}");

    expect(screen.queryByRole("textbox", { name: "inside the third" })).toBeNull();
    expect(helper("The third")).toHaveAttribute("aria-expanded", "false");
    expect(helper("The third")).toHaveFocus();
  });

  test("test_the_page_can_close_what_is_open_from_a_part_it_draws_outside_and_the_focus_goes_to_the_helper", async () => {
    // A page may draw a part of what a helper opens outside the helpers, where it stays
    // when they go. From there the page closes the helper as Escape does.
    const heard = jest.fn();
    function Page() {
      const [open, setOpen] = useState<Id | null>(null);
      const helping = useRef<HelpersHandle>(null);
      return (
        <>
          <Helpers
            ref={helping}
            label="Ways in"
            helpers={THREE}
            open={open}
            onOpen={(id) => {
              heard(id);
              setOpen(id);
            }}
          />
          <button type="button" onClick={() => helping.current?.close()}>
            outside
          </button>
        </>
      );
    }
    render(<Page />);
    const press = user();

    // While every helper is closed there is nothing to close, and the focus is left where it is.
    await press.click(screen.getByRole("button", { name: "outside" }));
    expect(heard).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "outside" })).toHaveFocus();

    await press.click(helper("The third"));
    await press.click(screen.getByRole("button", { name: "outside" }));

    expect(heard.mock.calls).toEqual([["three"], [null]]);
    expect(screen.queryByRole("textbox", { name: "inside the third" })).toBeNull();
    expect(helper("The third")).toHaveAttribute("aria-expanded", "false");
    expect(helper("The third")).toHaveFocus();
  });

  test("test_escape_closes_nothing_while_nothing_is_open", async () => {
    const heard = jest.fn();
    render(<Held heard={heard} />);
    const press = user();
    await press.tab();

    await press.keyboard("{Escape}");

    expect(heard).not.toHaveBeenCalled();
    expect(helper("The first")).toHaveFocus();
  });

  test("test_a_helper_can_be_opened_and_what_it_holds_reached_by_keyboard_alone", async () => {
    render(<Held />);
    const press = user();

    await press.tab();
    await press.tab();
    expect(helper("The second")).toHaveFocus();
    await press.tab();
    await press.keyboard("{Enter}");
    expect(helper("The third")).toHaveAttribute("aria-expanded", "true");
    // What was opened is the next stop after the line.
    await press.tab();

    expect(screen.getByRole("textbox", { name: "inside the third" })).toHaveFocus();
  });

  test("test_nothing_opens_because_the_pointer_is_over_a_helper", async () => {
    render(<Held />);

    await user().hover(helper("The first"));

    expect(helper("The first")).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("button", { name: "inside the first" })).toBeNull();
  });

  test("test_a_helper_the_page_leaves_out_is_not_drawn_and_with_none_there_is_no_line", () => {
    const { rerender, container } = render(<Held helpers={THREE.slice(1)} />);

    expect(within(line()).getAllByRole("button").map((button) => button.textContent)).toEqual([
      "The second",
      "The third",
    ]);

    rerender(<Held helpers={[]} />);
    expect(screen.queryByRole("group", { name: "Ways in" })).toBeNull();
    expect(container).toBeEmptyDOMElement();
  });

  test("test_with_scripts_off_the_page_as_it_is_built_holds_everything_the_helpers_hold", () => {
    // As the page is built: what a browser with scripts off is sent. No button of it can
    // open anything there, so what each helper holds stands in the page already.
    const built = renderToStaticMarkup(<Helpers label="Ways in" helpers={THREE} open={null} onOpen={() => undefined} />);
    const [drawn = "", unscripted = ""] = built.split("<noscript>");

    expect(built.split("<noscript>")).toHaveLength(2);
    for (const held of ["inside the first", "inside the second", "inside the third"]) {
      expect(unscripted.includes(held)).toBe(true);
      // A browser with scripts on is shown none of it until a helper is pressed.
      expect(drawn.includes(held)).toBe(false);
    }
    expect(unscripted.trimEnd().endsWith("</noscript></div>")).toBe(true);
    // In the order of the line.
    expect(unscripted.indexOf("inside the first")).toBeLessThan(unscripted.indexOf("inside the second"));
    expect(unscripted.indexOf("inside the second")).toBeLessThan(unscripted.indexOf("inside the third"));
  });

  test("test_closed_or_open_the_helpers_have_no_accessibility_fault", async () => {
    const { container } = render(<Held />);
    expect(await faultsIn(container)).toEqual([]);

    await user().click(helper("The first"));
    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("what a helper opens, which stands under its name", () => {
  /** A part that says what it is told of the helper it stands under. */
  function Told() {
    const under = useHelper();
    return <p data-told="">{under === null ? "under no helper" : `under "${under.says}", named by ${under.by}`}</p>;
  }
  const NAMED: readonly Helper<Id>[] = [
    { id: "one", label: "The first", children: <Told /> },
    { id: "two", label: "The second", children: <Told /> },
  ];

  test("test_it_is_told_which_helper_it_stands_under_so_that_it_need_not_say_the_name_a_second_time", async () => {
    // Seen in a browser: the shelf's own heading stood directly under the helper of the
    // same name, and the heading of the examples under the helper that offers one. Each
    // read as said twice.
    render(<Held helpers={NAMED} />);

    await user().click(helper("The second"));

    const button = helper("The second");
    expect(button.id).not.toBe("");
    expect(openedBy("The second").textContent).toBe(`under "The second", named by ${button.id}`);
    // Each helper has a name of its own to be named by.
    expect(new Set(within(line()).getAllByRole("button").map((one) => one.id)).size).toBe(2);
  });

  test("test_with_scripts_off_no_helper_is_drawn_over_it_and_it_is_told_of_none", () => {
    // The line of buttons is not drawn where a browser runs no script, so what each holds
    // stands under no name but its own.
    const html = renderToStaticMarkup(<Helpers label="Ways in" helpers={NAMED} open={null} onOpen={() => undefined} />);
    const kept = /<noscript>(.*)<\/noscript>/s.exec(html)?.[1] ?? "";

    expect(kept.match(/under no helper/g)).toHaveLength(2);
    expect(kept).not.toMatch(/named by/);
  });

  test("test_outside_the_helpers_a_part_is_under_no_helper", () => {
    render(<Told />);

    expect(screen.getByText("under no helper")).toBeInTheDocument();
  });
});

describe("what a helper opens, where the line stands low in the window", () => {
  // Both were asked for: that what a press opens is in sight, whole where it fits, and
  // that what was pressed stays under the hand. Under the line the two part wherever the
  // line stands low. Measured at 1440 by 900: "Try an example" was pressed at 793 and what
  // it opened was 310 px high, with 43 px of it in sight. On a phone 844 px high the line
  // stood at 747, and what it opened began under the foot of the window.
  const opened = () =>
    [...(line().parentElement?.children ?? [])].find((part) => part.id !== "" && !part.hasAttribute("hidden")) ?? null;
  const browser = (sizes: Sizes) => laidOut(sizes, { line, opened });
  /** A phone, with the line at the foot of the first screen, and what the first helper opens. */
  const A_PHONE: Sizes = { window: 844, line: 747, lineHigh: 44, opens: 338 };

  test("test_what_a_hand_opens_stands_over_the_line_where_it_has_no_room_under_it_and_the_helper_stays_where_it_was_pressed", async () => {
    render(<Held />);
    const laid = browser(A_PHONE);
    try {
      expect(laid.stands(helper("The first"))).toEqual([747, 791]);

      await user().click(helper("The first"));

      expect(openedBy("The first")).toBeVisible();
      // It comes before the line in the page, so that the keys go down the page as it is drawn.
      expect(comesBefore(openedBy("The first"), line())).toBe(true);
      // The page went on by as much as was put over the line, and the helper is where it was.
      expect(laid.asked).toEqual([338 + 12]);
      expect(laid.stands(helper("The first"))).toEqual([747, 791]);
      // What it opened is whole and in sight, over the line.
      expect(laid.stands(openedBy("The first"))).toEqual([747 - 12 - 338, 747 - 12]);
      expect(helper("The first")).toHaveFocus();
    } finally {
      laid.putBack();
    }
  });

  test("test_where_it_has_room_under_the_line_it_stands_there_and_nothing_is_moved", async () => {
    render(<Held />);
    const laid = browser({ ...A_PHONE, line: 300 });
    try {
      await user().click(helper("The second"));

      expect(comesBefore(line(), openedBy("The second"))).toBe(true);
      expect(laid.asked).toEqual([]);
      expect(laid.stands(helper("The second"))).toEqual([300, 344]);
      expect(laid.stands(openedBy("The second"))).toEqual([356, 694]);
    } finally {
      laid.putBack();
    }
  });

  test("test_where_it_has_room_neither_way_it_stands_under_and_its_head_is_brought_into_sight", async () => {
    // What is higher than the window has room on neither side of what opens it.
    render(<Held />);
    const laid = browser({ ...A_PHONE, line: 790, opens: 1170 });
    try {
      await user().click(helper("The first"));

      expect(comesBefore(line(), openedBy("The first"))).toBe(true);
      expect(laid.asked).toEqual([790 + 44 + 12 + HEAD - 844]);
    } finally {
      laid.putBack();
    }
  });

  test("test_closed_by_its_helper_what_stood_over_the_line_goes_and_the_helper_stays_where_it_was_pressed", async () => {
    render(<Held />);
    const laid = browser(A_PHONE);
    try {
      const press = user();
      await press.click(helper("The first"));
      laid.asked.length = 0;

      await press.click(helper("The first"));

      expect(helper("The first")).toHaveAttribute("aria-expanded", "false");
      expect(laid.asked).toEqual([-(338 + 12)]);
      expect(laid.stands(helper("The first"))).toEqual([747, 791]);
    } finally {
      laid.putBack();
    }
  });

  test("test_closed_by_escape_what_stood_over_the_line_goes_and_the_line_stays_where_it_stood", async () => {
    render(<Held />);
    const laid = browser(A_PHONE);
    try {
      const press = user();
      await press.click(helper("The third"));
      laid.asked.length = 0;

      await press.keyboard("{Escape}");

      expect(helper("The third")).toHaveAttribute("aria-expanded", "false");
      expect(helper("The third")).toHaveFocus();
      expect(laid.stands(helper("The third"))).toEqual([747, 791]);
    } finally {
      laid.putBack();
    }
  });

  test("test_another_helper_that_is_pressed_stays_where_it_was_pressed_as_what_it_opens_takes_the_place_of_the_first", async () => {
    render(<Held />);
    const laid = browser(A_PHONE);
    try {
      const press = user();
      await press.click(helper("The first"));

      await press.click(helper("The second"));

      expect(helper("The second")).toHaveAttribute("aria-expanded", "true");
      expect(comesBefore(openedBy("The second"), line())).toBe(true);
      expect(laid.stands(helper("The second"))).toEqual([747, 791]);
    } finally {
      laid.putBack();
    }
  });

  test("test_where_the_person_has_moved_the_page_since_it_stands_where_there_is_room_as_the_line_now_stands", async () => {
    render(<Held />);
    const laid = browser(A_PHONE);
    try {
      const press = user();
      await press.click(helper("The first"));
      await press.click(helper("The first"));
      // The person scrolls until the line stands near the top of the window.
      laid.scrollBy(647);
      laid.asked.length = 0;
      expect(laid.stands(helper("The first"))).toEqual([100, 144]);

      await press.click(helper("The first"));

      expect(comesBefore(line(), openedBy("The first"))).toBe(true);
      expect(laid.asked).toEqual([]);
    } finally {
      laid.putBack();
    }
  });

  test("test_what_the_keys_open_stands_under_the_line_and_the_whole_of_it_is_brought_into_sight", async () => {
    // Nobody's hand is on what was pressed, and whoever goes by the order of the page finds
    // what a button opens after the button.
    render(<Held />);
    const laid = browser(A_PHONE);
    try {
      const press = user();
      await press.tab();
      await press.keyboard("{Enter}");

      expect(helper("The first")).toHaveAttribute("aria-expanded", "true");
      expect(comesBefore(line(), openedBy("The first"))).toBe(true);
      // Until its foot is in sight, with a little room under it.
      expect(laid.asked).toEqual([747 + 44 + 12 + 338 + 8 - 844]);
      expect(laid.stands(helper("The first"))[0]).toBeGreaterThan(0);
      expect(helper("The first")).toHaveFocus();
    } finally {
      laid.putBack();
    }
  });

  test("test_nothing_is_moved_for_a_helper_that_the_page_opens_of_itself_and_what_it_holds_stands_under_the_line", () => {
    // A page may draw the helpers with one open, as it does when it is drawn again. Nobody
    // pressed anything, and the page stays where the person is reading.
    render(<Helpers label="Ways in" helpers={THREE} open="two" onOpen={() => undefined} />);
    const laid = browser(A_PHONE);
    try {
      expect(openedBy("The second")).toBeVisible();
      expect(comesBefore(line(), openedBy("The second"))).toBe(true);
      expect(laid.asked).toEqual([]);
    } finally {
      laid.putBack();
    }
  });

  test("test_what_is_open_over_the_line_has_no_accessibility_fault", async () => {
    const { container } = render(<Held />);
    const laid = browser(A_PHONE);
    try {
      await user().click(helper("The first"));
      expect(comesBefore(openedBy("The first"), line())).toBe(true);
    } finally {
      laid.putBack();
    }
    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("the other way it was built: what a helper opens stands under the line, always", () => {
  /**
   * Stands the line of helpers and what one opens in a window, as a browser that lays them
   * out would, and hears how far the page is asked to scroll. jsdom lays nothing out, and
   * scrolls nothing.
   */
  function standing(at: { readonly helper: readonly [number, number]; readonly opened: readonly [number, number] }) {
    const asked: number[] = [];
    const high = window.innerHeight;
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 844 });
    const measure = jest.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (
      this: HTMLElement,
    ) {
      const [top, foot] = this.tagName === "BUTTON" ? at.helper : this.hasAttribute("hidden") ? [0, 0] : at.opened;
      return { top, bottom: foot, left: 0, right: 0, x: 0, y: top, width: 0, height: foot - top, toJSON: () => ({}) };
    });
    const scroll = jest.spyOn(window, "scrollBy").mockImplementation(((_: number, y: number) => {
      asked.push(y);
    }) as typeof window.scrollBy);
    return {
      asked,
      putBack: () => {
        Object.defineProperty(window, "innerHeight", { configurable: true, value: high });
        measure.mockRestore();
        scroll.mockRestore();
      },
    };
  }

  test("test_what_a_helper_opens_is_brought_into_sight_where_it_begins_under_the_foot_of_the_window", async () => {
    // Seen on a phone, 390 by 844: the line stood at the foot of the first screen, from
    // 747, and what a helper opened began at 855. The helper turned amber, its arrow turned
    // down, and nothing else was seen to happen.
    const { asked, putBack } = standing({ helper: [747, 791], opened: [855, 1211] });
    try {
      render(<Held opens="under" />);

      await user().click(helper("The first"));

      expect(openedBy("The first")).toBeVisible();
      // Only as far as shows its head. Seen at 1440 by 900, while the whole of it was
      // brought into sight: the helper went 274 px from under the pointer, and an example
      // lay there in its place.
      expect(asked).toEqual([855 + HEAD - 844]);
      // The helper takes the focus where it stands, as it did: it is the page that is moved,
      // once the press has landed, and not the browser that moves it for the focus.
      expect(helper("The first")).toHaveFocus();
    } finally {
      putBack();
    }
  });

  test("test_what_opens_in_sight_moves_nothing", async () => {
    const { asked, putBack } = standing({ helper: [300, 344], opened: [356, 700] });
    try {
      render(<Held opens="under" />);

      await user().click(helper("The second"));

      expect(asked).toEqual([]);
    } finally {
      putBack();
    }
  });

  test("test_what_opens_with_its_head_in_sight_leaves_the_helper_under_the_hand", async () => {
    // The rest of what it opened is under the foot of the window, and is the person's to
    // scroll to: the helper that was pressed stays where it was pressed.
    const { asked, putBack } = standing({ helper: [740, 784], opened: [796, 1152] });
    try {
      render(<Held opens="under" />);

      await user().click(helper("The first"));

      expect(openedBy("The first")).toBeVisible();
      expect(asked).toEqual([]);
    } finally {
      putBack();
    }
  });

  test("test_a_helper_that_is_opened_by_keyboard_brings_what_it_opens_into_sight_too", async () => {
    const { asked, putBack } = standing({ helper: [747, 791], opened: [855, 1211] });
    try {
      render(<Held opens="under" />);
      const press = user();

      await press.tab();
      await press.keyboard("{Enter}");

      expect(helper("The first")).toHaveAttribute("aria-expanded", "true");
      expect(asked).toEqual([855 + HEAD - 844]);
    } finally {
      putBack();
    }
  });

  test("test_nothing_is_moved_when_a_helper_is_closed_by_a_press_or_by_escape", async () => {
    const { asked, putBack } = standing({ helper: [747, 791], opened: [855, 1211] });
    try {
      render(<Held opens="under" />);
      const press = user();
      await press.click(helper("The first"));
      asked.length = 0;

      await press.click(helper("The first"));
      expect(helper("The first")).toHaveAttribute("aria-expanded", "false");
      expect(asked).toEqual([]);

      await press.click(helper("The third"));
      asked.length = 0;
      await press.keyboard("{Escape}");
      expect(helper("The third")).toHaveAttribute("aria-expanded", "false");
      expect(asked).toEqual([]);
    } finally {
      putBack();
    }
  });

  test("test_nothing_is_moved_for_a_helper_that_the_page_opens_of_itself", () => {
    // A page may draw the helpers with one open, as it does when it is drawn again. Nobody
    // pressed anything, and the page stays where the person is reading.
    const { asked, putBack } = standing({ helper: [747, 791], opened: [855, 1211] });
    try {
      render(<Helpers label="Ways in" helpers={THREE} open="two" opens="under" onOpen={() => undefined} />);

      expect(openedBy("The second")).toBeVisible();
      expect(asked).toEqual([]);
    } finally {
      putBack();
    }
  });
});

const RULES = rulesOf(readFileSync(path.join(__dirname, "Helpers.module.css"), "utf8"));
const setsOf = (selector: string, under: string | null = null) =>
  new Map(RULES.filter((rule) => rule.selector === selector && rule.under === under).flatMap((rule) => [...rule.sets]));
const WELCOME = "@media (prefers-reduced-motion: no-preference)";
/** The face of a helper: what is drawn of it, inside the button. */
const faceOf = (name: string) => helper(name).firstElementChild as HTMLElement;

describe("a helper, as the look draws it", () => {
  test("test_the_helper_that_is_open_is_amber_and_the_rest_are_cream", async () => {
    render(<Held />);
    await user().click(helper("The second"));

    expect(["The first", "The second", "The third"].map((name) => faceOf(name).getAttribute("data-open"))).toEqual([
      "false",
      "true",
      "false",
    ]);
    // Each is drawn by the picture of a button of the look: amber for what is open, by its two pictures.
    expect(faceOf("The second").style.getPropertyValue("--face")).toBe('url("/art/ui-button-on.png")');
    expect(faceOf("The second").style.getPropertyValue("--face-down")).toBe('url("/art/ui-button-on-down.png")');
    expect(faceOf("The first").style.getPropertyValue("--face")).toBe('url("/art/ui-button.png")');
    expect(faceOf("The first").style.getPropertyValue("--face-down")).toBe('url("/art/ui-button-down.png")');
    expect(setsOf('.face[data-open="true"]').get("background-color")).toBe("var(--chosen)");
    expect(setsOf('.face[data-open="true"]').get("color")).toBe("var(--on-chosen)");
    // No helper is cobalt: Search is the one button of the page that is.
    expect(RULES.filter((rule) => [...rule.sets.values()].some((value) => /--(accent|cobalt)\b/.test(value)))).toEqual([]);
  });

  test("test_a_helper_says_that_it_is_open_and_never_that_it_is_pressed", async () => {
    // What is open is amber, as what is on is. It is no choice that is made: it opens what
    // stands under it, and says that, as it did.
    render(<Held />);
    await user().click(helper("The second"));

    for (const button of within(line()).getAllByRole("button")) {
      expect(button).toHaveAttribute("aria-expanded");
      expect(button).not.toHaveAttribute("aria-pressed");
    }
    expect(helper("The second")).toHaveAttribute("aria-expanded", "true");
  });

  test("test_the_button_stands_under_a_press_and_its_face_steps_into_its_shadow", () => {
    const pressed = RULES.filter((rule) => /:active/.test(rule.selector));

    // Under a press the picture gives way to the picture of the button pressed, which is
    // of one size with it. Nothing is set on the button itself.
    expect(pressed.map((rule) => [rule.selector, rule.under, [...rule.sets.keys()]])).toEqual([
      [".helper:active > .face", null, ["border-image-source"]],
      [".helper:active > .face > .says", WELCOME, ["transform"]],
      [".helper:active > .face", "@media (forced-colors: active)", ["border-image-source"]],
    ]);
    expect(setsOf(".helper:active > .face").get("border-image-source")).toBe("var(--face-down)");
    // What it says steps with the face, by one art pixel, where movement is welcome.
    expect(setsOf(".helper:active > .face > .says", WELCOME).get("transform")).toBe("translate(var(--px), var(--px))");
    // Nothing else comes or goes with the pointer or the focus.
    expect(RULES.filter((rule) => /:(hover|focus)/.test(rule.selector))).toEqual([]);
  });

  test("test_a_helper_is_as_large_as_a_main_control_and_its_shadow_is_its_own_room", () => {
    const face = setsOf(".face");

    expect(setsOf(".helper").get("padding")).toBe("0");
    expect(setsOf(".helper").get("border")).toBe("0");
    // The picture is cut where the picture of every button of the look is cut: three art
    // pixels at the top and the sides, and four at the foot, where its shadow lies.
    expect(face.get("border-width")).toBe("calc(var(--px) * 3) calc(var(--px) * 3) calc(var(--px) * 4)");
    expect(face.get("border-image")).toBe(
      "var(--face) 3 3 4 3 fill / calc(var(--px) * 3) calc(var(--px) * 3) calc(var(--px) * 4) repeat",
    );
    expect(face.get("image-rendering")).toBe("pixelated");
    // Under the picture is a plain edge of ink on cream, which is what is drawn before it comes.
    expect([face.get("border-color"), face.get("background-color"), face.get("background-clip")]).toEqual([
      "var(--ink)",
      "var(--page)",
      "padding-box",
    ]);
    render(<Held />);
    for (const button of within(line()).getAllByRole("button")) expect(button).toHaveClass("target");
  });

  test("test_its_words_are_a_short_label_in_the_face_of_names", () => {
    expect(setsOf(".helper").get("font")).toBe("400 var(--name-1) / 1 var(--font-name)");
    expect(setsOf(".helper").get("font-synthesis")).toBe("none");
  });

  test("test_the_arrow_stands_after_the_words_and_points_down_while_a_helper_is_closed_and_up_while_it_is_open", async () => {
    // The founder, of the settings: "place the arrow to the right of the button and make it
    // clearer that they are collapsable". Seen by three people since: the two helpers kept
    // the arrow before their words, pointing at them, where every other fold of the website
    // has it at its far end. What opens in place says so by one sign, in one place.
    render(<Held />);
    const mark = () => helper("The second").querySelector("[aria-hidden='true']") as HTMLElement;

    // One drawing, which is for the eye: the button says whether it is open.
    expect(mark().style.getPropertyValue("--arrow")).toBe('url("/art/ui-arrow.png")');
    expect(helper("The second").textContent).toBe("The second");
    // It comes after the words in the page, and is drawn where it comes: no rule puts it elsewhere.
    expect(mark().previousSibling?.textContent).toBe("The second");
    expect(mark().nextSibling).toBeNull();
    expect(RULES.filter((rule) => rule.sets.has("order") || /reverse/.test(rule.sets.get("flex-direction") ?? ""))).toEqual([]);
    const before = mark();
    await user().click(helper("The second"));
    expect(mark()).toBe(before);

    // It is drawn as it points up, which is what it says of what is open: and turned half
    // way round it points down, at what would open under it.
    expect(setsOf(".mark::before").get("rotate")).toBe("180deg");
    expect(setsOf('.helper[aria-expanded="true"] .mark::before').get("rotate")).toBe("none");
    // Its room is said once, of the mark, and is the same whichever way it points.
    expect([...setsOf('.helper[aria-expanded="true"] .mark::before').keys()]).toEqual(["rotate"]);
    expect([setsOf(".mark").get("width"), setsOf(".mark").get("height")]).toEqual([
      "calc(var(--px) * var(--arrow-w))",
      "calc(var(--px) * (var(--arrow-h) - 2))",
    ]);
    // It is turned at once: nothing of a helper moves over time.
    expect(RULES.filter((rule) => [...rule.sets.keys()].some((property) => /^(transition|animation)/.test(property)))).toEqual([]);
  });

  test("test_three_helpers_stand_on_one_line_beside_the_map_on_a_desk", () => {
    // Measured in a browser at 1440 by 900: the words of the three are 103, 127 and 152 px
    // wide, and the answer is 624 px. What a helper has beside its words is its edge, its
    // room, its arrow and the space after it. jsdom lays nothing out, so this holds what
    // the width depends on. Measure before adding to any of them.
    const px = Number.parseInt({ ...asWritten(), ...writtenForAWideScreen() }["--px"] ?? "", 10);
    const artPixels = (length: string | undefined) => Number(/\* (\d+)\)/.exec(length ?? "")?.[1] ?? Number.NaN);
    const edge = 2 * 3;
    const room = 2 * artPixels(setsOf(".face").get("padding"));
    const arrow = 10 + artPixels(setsOf(".says").get("gap"));
    const beside = (edge + room + arrow) * px;
    const between = 2 * 8;

    expect(px).toBe(3);
    expect(103 + 127 + 152 + 3 * beside + between).toBeLessThanOrEqual(624);
  });
});
