import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";

import { faultsIn } from "../../../test/support/axe";
import { heavier, rulesOf, weightOf } from "../../../test/support/css";
import { Press } from "../kit/Press/Press";
import { PlainPage } from "./PlainPage";

const RULES = rulesOf(readFileSync(path.join(__dirname, "PlainPage.module.css"), "utf8"));
const setsOf = (selector: string) =>
  new Map(RULES.filter((rule) => rule.selector === selector && rule.under === null).flatMap((rule) => [...rule.sets]));

function lost() {
  return render(
    <main>
      <PlainPage kind="lost" title="Page not found" text="There is no page at this address.">
        <Press kind="go" href="/">
          Go to the search
        </Press>
      </PlainPage>
    </main>,
  );
}

function fault(onPress = jest.fn()) {
  return render(
    <main>
      <PlainPage kind="fault" title="Something went wrong" text="This page could not be shown.">
        <Press kind="go" onPress={onPress}>
          Try again
        </Press>
      </PlainPage>
    </main>,
  );
}

function held() {
  return render(
    <main>
      <PlainPage kind="held" title="This page cannot be shown" text="Nothing is shown, so that no figure is read under the wrong notice." />
    </main>,
  );
}

describe("a page that says one thing", () => {
  test("test_it_is_one_box_on_the_meadow_and_tells_the_shell_to_draw_no_box_round_it", () => {
    const { container } = lost();
    const page = container.querySelector("main")?.firstElementChild as HTMLElement;

    // The shell draws no box round a page that says it stands boxes of its own.
    expect(page).toHaveAttribute("data-dressed");
    expect(page.children).toHaveLength(1);
    expect(page.firstElementChild).toHaveAttribute("data-kind", "box");
    // Every sentence and every link of the page stands in the box: nothing is read on the grass.
    const box = within(page.firstElementChild as HTMLElement);
    expect(box.getByRole("heading", { level: 1, name: "Page not found" })).toBeInTheDocument();
    expect(box.getByText("There is no page at this address.")).toBeInTheDocument();
    expect(box.getByRole("link", { name: "Go to the search" })).toHaveAttribute("href", "/");
  });

  test("test_it_lays_no_ground_over_its_box_and_cuts_nothing_off_at_its_edge", () => {
    const laid = RULES.filter((rule) => /\.(page|box)$/.test(rule.selector) && (rule.sets.has("background") || rule.sets.has("overflow")));

    expect(laid.map((rule) => rule.selector)).toEqual([]);
    // It is no wider than a sentence is read at, and is as wide as the page on a narrow screen.
    expect([setsOf(".page > .box").get("width"), setsOf(".page > .box").get("max-width")]).toEqual(["100%", "40rem"]);
  });

  test("test_how_wide_the_box_is_does_not_hang_on_which_style_sheet_is_read_last", () => {
    // A box of the kit says that it is as wide as what holds it. Seen in the style sheets: a
    // rule of this sheet that weighs what the kit's weighs holds only if it is read after it.
    const kit = rulesOf(readFileSync(path.join(__dirname, "..", "kit", "Frame", "Frame.module.css"), "utf8"));
    const ofTheKit = kit.filter((rule) => rule.sets.has("max-width") || rule.sets.has("padding")).map((rule) => weightOf(rule.selector));
    const own = RULES.filter((rule) => rule.sets.has("max-width") || (rule.sets.has("padding") && /box/.test(rule.selector)));

    expect(ofTheKit.length).toBeGreaterThan(0);
    expect(own.length).toBeGreaterThan(0);
    for (const rule of own) {
      expect([rule.selector, ofTheKit.every((weight) => heavier(weightOf(rule.selector), weight))]).toEqual([rule.selector, true]);
    }
  });

  test("test_a_page_that_is_not_there_is_not_said_as_an_alert", () => {
    lost();

    expect(screen.queryByRole("alert")).toBeNull();
  });

  test("test_the_drawing_of_a_page_that_is_not_there_is_dress_and_says_nothing", () => {
    const { container } = lost();
    const drawn = [...container.querySelectorAll<HTMLElement>("[style*='/art/']")];

    expect(drawn.map((one) => /\/art\/([a-z0-9-]+)\.png/.exec(one.getAttribute("style") ?? "")?.[1])).toContain("key-blank");
    for (const one of drawn.filter((each) => each.closest("a, button") === null)) {
      expect(one).toHaveAttribute("aria-hidden", "true");
      expect(one).toBeEmptyDOMElement();
    }
    // Nothing of the page is a picture that is fetched as one: a drawing is a ground of a style sheet.
    expect([...container.querySelectorAll("img, svg, [src]")]).toEqual([]);
  });

  test("test_a_fault_is_said_at_once_in_the_words_it_is_given_and_nothing_else", () => {
    fault();

    const alert = screen.getByRole("alert");
    expect(alert).toHaveAttribute("data-kind", "box");
    expect(alert.textContent).toBe("Something went wrongThis page could not be shown.Try again");
  });

  test("test_a_fault_is_marked_by_a_square_of_poppy_inside_a_rule_of_ink_and_by_no_drawing", () => {
    const { container } = fault();
    const mark = setsOf(".mark");

    expect([mark.get("background"), mark.get("border")]).toEqual(["var(--error-edge)", "var(--edge) solid var(--border)"]);
    expect(container.querySelector("[aria-hidden='true']")).toBeEmptyDOMElement();
    // Burro is drawn beside no failure, and nothing here pictures a person.
    expect(container.innerHTML.includes("/art/burro")).toBe(false);
    expect(container.innerHTML.includes("/art/key-blank")).toBe(false);
  });

  test("test_a_page_that_is_held_back_is_said_at_once_is_marked_as_a_notice_is_and_offers_no_way_on", () => {
    const { container } = held();

    const alert = screen.getByRole("alert");
    expect(alert.textContent).toBe("This page cannot be shownNothing is shown, so that no figure is read under the wrong notice.");
    expect(within(alert).getByRole("heading", { level: 1, name: "This page cannot be shown" })).toBeInTheDocument();
    // There is nothing to press, and no room is kept for what is not there.
    expect([...container.querySelectorAll("a, button")]).toEqual([]);
    expect(alert.children).toHaveLength(2);
    // It is no failure: its mark is the amber of a notice, inside the same rule of ink.
    expect(alert).toHaveAttribute("data-says", "held");
    expect(setsOf('[data-says="held"] .mark').get("background")).toBe("var(--notice-mark)");
  });

  test("test_the_way_on_is_one_button_of_full_size_and_does_what_it_is_for", () => {
    const onPress = jest.fn();
    fault(onPress);

    const retry = screen.getByRole("button", { name: "Try again" });
    retry.click();

    expect(screen.getAllByRole("button")).toHaveLength(1);
    expect(retry).toHaveClass("target");
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  test("test_the_heading_is_a_name_and_what_it_says_is_a_sentence", () => {
    // The heading is an `h1`, which the base sets in the face of names. Nothing here sets a face.
    const faces = RULES.filter((rule) => [...rule.sets.keys()].some((property) => /^font(-family)?$/.test(property)));

    expect(faces.map((rule) => rule.selector)).toEqual([]);
    expect(setsOf(".says").get("font-size")).toBe("var(--size-lead)");
  });

  test.each([
    ["a page that is not there", lost],
    ["a fault", fault],
    ["a page that is held back", held],
  ])("test_it_has_no_accessibility_fault: %s", async (_, show) => {
    const { container } = show();

    expect(await faultsIn(container)).toEqual([]);
  });
});
