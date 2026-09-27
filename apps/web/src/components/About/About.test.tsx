import { render, screen, within } from "@testing-library/react";

import { faultsIn } from "../../../test/support/axe";
import { About, Board, Boxed, Edged, Loose, Marked, Part, Points, Slip, Sourced } from "./About";
import { onTheGrass } from "./grass";

function page() {
  return render(
    <main>
      <About title="Methods" lead="How it is worked out." art="ui-key">
        <Part id="how" title="How it works">
          <p>It is worked out from what is published.</p>
          <Points points={["One thing.", "And another."]} />
        </Part>
        <Part id="wide" title="What is wide" lay="over" region={false}>
          <Board as="h3" id="one">
            One table
          </Board>
          <Edged>
            <table aria-labelledby="one">
              <thead>
                <tr>
                  <th scope="col">Setting</th>
                  <th scope="col">Counts for</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <th scope="row">A setting</th>
                  <td>30 of 100</td>
                </tr>
              </tbody>
            </table>
          </Edged>
        </Part>
        <Boxed>
          <p>What another part says.</p>
        </Boxed>
        <Slip>
          <p>Last updated: 26 September 2026</p>
        </Slip>
      </About>
    </main>,
  );
}

describe("a page that explains", () => {
  test("test_it_tells_the_shell_that_it_stands_boxes_of_its_own_on_the_grass", () => {
    const { container } = page();
    const root = container.querySelector("main")?.firstElementChild as HTMLElement;

    // The shell draws no box round a page that says so, on the child of `main`.
    expect(root).toHaveAttribute("data-dressed");
    expect(root.tagName).toBe("DIV");
  });

  test("test_its_heading_and_what_it_is_for_stand_in_the_first_box_of_the_page", () => {
    const { container } = page();
    const root = container.querySelector("[data-dressed]") as HTMLElement;
    const head = root.firstElementChild as HTMLElement;

    expect(head).toHaveAttribute("data-kind", "box");
    expect(within(head).getByRole("heading", { level: 1, name: "Methods" })).toBeInTheDocument();
    expect(within(head).getByText("How it is worked out.").tagName).toBe("P");
    // It is the one main heading, and is no landmark of its own: the page has its header.
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(head.tagName).toBe("DIV");
  });

  test("test_a_part_that_a_link_leads_to_takes_the_focus_at_its_heading_and_is_no_stop_of_the_keyboard", () => {
    // A link that leads to a part brings the part into sight. Whoever hears the page is
    // brought there too: the heading takes the focus, so that it is what is read next.
    render(
      <About title="Methods" lead="How it is worked out.">
        <Part id="led-to" title="A part that a link leads to" led>
          <p>What it says.</p>
        </Part>
        <Part id="read" title="A part that is read">
          <p>What it says.</p>
        </Part>
      </About>,
    );
    const [led, read] = [document.getElementById("led-to"), document.getElementById("read")];

    expect([led?.tagName, led?.getAttribute("tabindex")]).toEqual(["H2", "-1"]);
    expect(read?.hasAttribute("tabindex")).toBe(false);
    led?.focus();
    expect(led).toHaveFocus();
    // No key of the keyboard stops at it: it is reached by the link that leads to it.
    expect(document.querySelectorAll("[tabindex]:not([tabindex='-1'])")).toHaveLength(0);
  });

  test("test_the_drawing_beside_the_heading_is_dress_and_says_nothing", () => {
    const { container } = page();
    const head = container.querySelector("[data-dressed]")?.firstElementChild as HTMLElement;
    const drawn = [...head.querySelectorAll<HTMLElement>("[style*='/art/']")];

    expect(drawn.map((one) => /\/art\/([a-z0-9-]+)\.png/.exec(one.getAttribute("style") ?? "")?.[1])).toEqual(["ui-key"]);
    for (const one of drawn) {
      expect(one).toHaveAttribute("aria-hidden", "true");
      expect(one).toBeEmptyDOMElement();
    }
    // The heading is named by its words alone.
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Methods");
    // It stands directly before the heading, and what holds the two says that one is drawn.
    expect(drawn[0]?.nextElementSibling).toBe(screen.getByRole("heading", { level: 1 }));
    expect(drawn[0]?.parentElement).toHaveAttribute("data-drawn", "true");
    // Nothing of the page is a picture that is fetched as one: a drawing is a ground of a style sheet.
    expect([...container.querySelectorAll("img, svg, [src]")]).toEqual([]);
  });

  test("test_a_page_with_no_drawing_has_none", () => {
    const { container } = render(
      <About title="Vibes" lead="What a vibe is.">
        <Slip>
          <p>A line.</p>
        </Slip>
      </About>,
    );

    expect(container.querySelector("[style*='/art/']")).toBeNull();
    expect(screen.getByRole("heading", { level: 1 }).parentElement).toHaveAttribute("data-drawn", "false");
  });

  test("test_every_sentence_of_the_page_stands_in_a_box_of_cream_and_none_on_the_grass", () => {
    const { container } = page();

    expect(onTheGrass(container.querySelector("[data-dressed]") as HTMLElement)).toEqual([]);
    // It bites: a sentence set straight on the page is found.
    const { container: bare } = render(
      <About title="Vibes" lead="What a vibe is.">
        <p>A sentence on the grass.</p>
      </About>,
    );
    expect(onTheGrass(bare.querySelector("[data-dressed]") as HTMLElement)).toEqual(["A sentence on the grass."]);
  });
});

describe("a part of a page that explains", () => {
  test("test_a_part_is_a_box_named_by_its_heading_which_another_page_may_lead_to", () => {
    page();

    const part = screen.getByRole("region", { name: "How it works" });

    expect(part).toHaveAttribute("data-kind", "box");
    expect(part.tagName).toBe("SECTION");
    // The heading is the part's own child, so that what is said of a heading's part is said of it.
    const heading = within(part).getByRole("heading", { level: 2, name: "How it works" });
    expect(heading).toHaveAttribute("id", "how");
    expect(heading.parentElement).toBe(part);
    expect(part).toHaveTextContent("It is worked out from what is published.");
  });

  test("test_a_part_that_was_no_landmark_of_the_page_is_none_now", () => {
    const { container } = page();

    const heading = screen.getByRole("heading", { level: 2, name: "What is wide" });

    expect(screen.queryByRole("region", { name: "What is wide" })).toBeNull();
    expect(heading.parentElement?.tagName).toBe("DIV");
    expect(heading.parentElement).toHaveAttribute("data-kind", "box");
    expect(container.querySelectorAll("section")).toHaveLength(1);
  });

  test("test_a_part_says_whether_its_heading_stands_beside_what_is_read_or_over_it", () => {
    page();

    expect(screen.getByRole("region", { name: "How it works" })).toHaveAttribute("data-lay", "beside");
    expect(screen.getByRole("heading", { level: 2, name: "What is wide" }).parentElement).toHaveAttribute("data-lay", "over");
  });

  test("test_the_points_of_a_part_are_a_list_in_the_order_they_were_given", () => {
    page();

    const list = within(screen.getByRole("region", { name: "How it works" })).getByRole("list");

    expect(within(list).getAllByRole("listitem").map((item) => item.textContent)).toEqual(["One thing.", "And another."]);
  });

  test("test_a_small_heading_is_a_heading_of_the_rank_it_is_given", () => {
    page();

    expect(screen.getByRole("heading", { level: 3, name: "One table" })).toHaveAttribute("id", "one");
  });

  test("test_a_table_stands_inside_a_plain_edge_of_ink_and_keeps_its_name", () => {
    page();

    const table = screen.getByRole("table", { name: "One table" });

    expect(table.parentElement).toHaveAttribute("data-kind", "plain");
    expect(within(table).getAllByRole("row")).toHaveLength(2);
  });

  test("test_what_another_part_draws_is_given_a_box_and_a_loose_line_a_slip", () => {
    page();

    expect(screen.getByText("What another part says.").parentElement).toHaveAttribute("data-kind", "box");
    expect(screen.getByText("Last updated: 26 September 2026").parentElement).toHaveAttribute("data-kind", "plain");
  });

  test("test_what_another_hand_draws_is_held_as_it_came_and_given_no_ground_it_did_not_ask_for", () => {
    const { container } = render(
      <Loose>
        <ul>
          <li>A source</li>
        </ul>
      </Loose>,
    );

    const held = container.firstElementChild as HTMLElement;
    expect(held.tagName).toBe("DIV");
    expect(held).not.toHaveAttribute("data-kind");
    // It says that it holds what is another's, so that what is held to the page is not held against it.
    expect(held).toHaveAttribute("data-held", "as-it-came");
    expect(held.children).toHaveLength(1);
    expect(held.firstElementChild?.tagName).toBe("UL");
  });

  test("test_a_list_of_a_part_holds_the_lines_it_is_given_and_is_a_list_to_whoever_hears_the_page", () => {
    render(
      <Marked>
        <li>
          <a href="#a-vibe">A vibe</a>: what it counts
        </li>
      </Marked>,
    );

    expect(within(screen.getByRole("list")).getAllByRole("listitem").map((item) => item.textContent)).toEqual(["A vibe: what it counts"]);
  });

  test("test_the_sources_of_a_thing_stand_after_the_key_of_the_look_which_says_nothing_and_opens_nothing", () => {
    const { container } = render(
      <Sourced>
        <li>
          <a href="#one">One source</a>
        </li>
        <li>
          <a href="#another">Another</a>
        </li>
      </Sourced>,
    );
    const key = container.querySelector<HTMLElement>("[style*='/art/']");

    expect(key?.style.getPropertyValue("--art")).toBe('url("/art/ui-key.png")');
    expect(key).toHaveAttribute("aria-hidden", "true");
    expect(key).toBeEmptyDOMElement();
    // It is no button and no link: on a page that is built ahead of time a source is written out.
    expect(container.querySelectorAll("button, summary")).toHaveLength(0);
    expect(key?.closest("a")).toBeNull();
    // The sources are a list, each one press from its entry, in the order they were given.
    expect(key?.nextElementSibling).toBe(screen.getByRole("list"));
    expect(screen.getAllByRole("link").map((link) => [link.textContent, link.getAttribute("href")])).toEqual([
      ["One source", "#one"],
      ["Another", "#another"],
    ]);
  });

  test("test_the_page_has_no_accessibility_fault", async () => {
    const { container } = page();

    expect(await faultsIn(container, { wholePage: true })).toEqual([]);
  });
});
