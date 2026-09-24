import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { faultsIn } from "../../../test/support/axe";
import { Disclosure } from "./Disclosure";

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
