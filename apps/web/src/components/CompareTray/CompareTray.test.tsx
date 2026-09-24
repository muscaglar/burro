import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { COMPARE, TRAY } from "@/content/compare";
import { recordedAnswer } from "@/lib/api/recorded";
import { SessionProvider } from "@/lib/session/session";

import { faultsIn } from "../../../test/support/axe";
import { watch } from "../../../test/support/watch";
import { CompareButton } from "./CompareButton";
import { CompareTray, trayStatus } from "./CompareTray";

const areas = recordedAnswer("list_areas", "areas").body.data.areas;

function show(count = 5) {
  const user = userEvent.setup({ delay: null });
  const view = render(
    <SessionProvider>
      <CompareTray />
      <ul>
        {areas.slice(0, count).map((area) => (
          <li key={area.area_id}>
            <CompareButton area={area} />
          </li>
        ))}
      </ul>
    </SessionProvider>,
  );
  return { user, ...view };
}

const tray = () => screen.getByRole("region", { name: TRAY.title });
const add = (at: number) => screen.getByRole("button", { name: COMPARE.add(areas[at]?.name ?? "") });
const link = () => within(tray()).queryByRole("link");

describe("the tray of areas to compare", () => {
  test("test_the_tray_has_its_place_before_anything_is_chosen", () => {
    show();

    expect(tray()).toHaveTextContent(TRAY.none);
    expect(link()).toBeNull();
    expect(within(tray()).queryByRole("list")).toBeNull();
  });

  test("test_one_area_is_not_enough_to_compare_and_the_tray_says_so", async () => {
    const { user } = show();

    await user.click(add(0));

    expect(within(tray()).getByRole("status")).toHaveTextContent(TRAY.one);
    expect(link()).toBeNull();
  });

  test("test_two_areas_can_be_compared_and_the_link_holds_their_slugs_and_nothing_else", async () => {
    const { user } = show();

    await user.click(add(0));
    await user.click(add(1));

    expect(link()).toHaveTextContent(TRAY.go(2));
    expect(link()).toHaveAttribute("href", `/compare?a=${areas[0]?.slug}&a=${areas[1]?.slug}`);
    // It is followed when it is pressed, and not fetched before.
    expect(link()).toHaveAttribute("data-prefetch", "false");
  });

  test("test_the_areas_are_in_the_order_they_were_chosen", async () => {
    const { user } = show();

    await user.click(add(2));
    await user.click(add(0));

    expect(within(tray()).getAllByRole("listitem").map((item) => item.textContent)).toEqual(
      [areas[2], areas[0]].map((area) => `${area?.name}×`),
    );
    expect(link()).toHaveAttribute("href", `/compare?a=${areas[2]?.slug}&a=${areas[0]?.slug}`);
  });

  test("test_a_fifth_area_cannot_be_added_and_the_tray_says_why", async () => {
    const { user } = show();
    for (const at of [0, 1, 2, 3]) await user.click(add(at));

    expect(add(4)).toBeDisabled();
    expect(within(tray()).getByRole("status")).toHaveTextContent(TRAY.full);
    expect(link()).toHaveTextContent(TRAY.go(4));
    // One that is chosen can still be taken out.
    expect(screen.getByRole("button", { name: COMPARE.remove(areas[0]?.name ?? "") })).toBeEnabled();
  });

  test("test_a_button_that_is_switched_off_says_why_where_it_stands", async () => {
    // Seen in a browser: with four areas chosen the button of a fifth was switched off, and
    // the reason was in the tray, 5,570 pixels up the page. Nothing beside the button said why.
    const { user } = show();
    for (const at of [0, 1, 2, 3]) await user.click(add(at));

    const fifth = add(4);
    expect(fifth).toBeDisabled();
    expect(fifth).toHaveAccessibleDescription(TRAY.full);
    const why = within(fifth.closest("li") as HTMLElement).getByText(TRAY.full);
    expect(why.closest(".visually-hidden, [aria-hidden='true'], [hidden]")).toBeNull();
    // A button that can be pressed says nothing of it.
    await user.click(screen.getByRole("button", { name: COMPARE.remove(areas[0]?.name ?? "") }));
    expect(add(4)).not.toHaveAccessibleDescription();
  });

  test("test_the_way_to_the_comparison_is_beside_the_button_of_an_area_that_is_chosen", async () => {
    // Seen in a browser: the link that compares the areas was in the tray alone, thousands
    // of pixels from the buttons that fill it.
    const user = userEvent.setup({ delay: null });
    render(
      <SessionProvider>
        <CompareTray />
        <ul>
          {areas.slice(0, 3).map((area) => (
            <li key={area.area_id}>
              <CompareButton area={area} far />
            </li>
          ))}
        </ul>
      </SessionProvider>,
    );
    const item = (at: number) =>
      within(screen.getByRole("button", { name: new RegExp(`${areas[at]?.name} (to|from) compare$`) }).closest("li") as HTMLElement);

    await user.click(add(0));
    // One area is not enough, and the button's own line says so.
    expect(item(0).getByText(TRAY.one)).toBeInTheDocument();
    expect(item(0).queryByRole("link")).toBeNull();

    await user.click(add(1));
    for (const at of [0, 1]) {
      const near = item(at).getByRole("link", { name: TRAY.go(2) });
      expect(near).toHaveAttribute("href", `/compare?a=${areas[0]?.slug}&a=${areas[1]?.slug}`);
      expect(near).toHaveAttribute("data-prefetch", "false");
      expect(near).toHaveClass("target");
    }
    // An area that is not chosen has the button and nothing more.
    expect(item(2).queryByRole("link")).toBeNull();
  });

  test("test_beside_the_tray_the_button_does_not_say_again_what_the_tray_says", async () => {
    const { user } = show();

    await user.click(add(0));
    await user.click(add(1));

    expect(screen.getAllByRole("link", { name: TRAY.go(2) })).toHaveLength(1);
  });

  test("test_the_button_says_what_it_would_do_so_that_chosen_is_never_told_by_colour_alone", async () => {
    const { user } = show();

    await user.click(add(0));

    expect(screen.queryByRole("button", { name: COMPARE.add(areas[0]?.name ?? "") })).toBeNull();
    await user.click(screen.getByRole("button", { name: COMPARE.remove(areas[0]?.name ?? "") }));
    expect(add(0)).toBeInTheDocument();
    expect(tray()).toHaveTextContent(TRAY.none);
  });

  test("test_an_area_can_be_taken_out_from_the_tray_and_the_tray_can_be_cleared", async () => {
    const { user } = show();
    for (const at of [0, 1, 2]) await user.click(add(at));

    await user.click(within(tray()).getByRole("button", { name: TRAY.remove(areas[1]?.name ?? "") }));
    expect(link()).toHaveAttribute("href", `/compare?a=${areas[0]?.slug}&a=${areas[2]?.slug}`);

    await user.click(within(tray()).getByRole("button", { name: TRAY.clear }));
    expect(tray()).toHaveTextContent(TRAY.none);
    expect(add(1)).toBeInTheDocument();
  });

  test("test_the_tray_can_be_used_by_keyboard_alone", async () => {
    const { user } = show(2);

    await user.tab();
    await user.keyboard("{Enter}");
    await user.tab();
    await user.keyboard(" ");

    expect(link()).toHaveTextContent(TRAY.go(2));
    // The focus stays on the button that was pressed.
    expect(screen.getByRole("button", { name: COMPARE.remove(areas[1]?.name ?? "") })).toHaveFocus();
  });

  test("test_every_control_of_the_tray_takes_a_target_size", async () => {
    const { user, container } = show();
    for (const at of [0, 1]) await user.click(add(at));

    const controls = [...container.querySelectorAll("a, button")];

    expect(controls.length).toBeGreaterThan(6);
    expect(controls.filter((control) => !control.classList.contains("target"))).toEqual([]);
  });

  test.each([0, 1, 2, 4])("test_the_tray_has_no_accessibility_fault_with_%i_chosen", async (count) => {
    const { user, container } = show();
    for (let at = 0; at < count; at += 1) await user.click(add(at));

    expect(await faultsIn(container)).toEqual([]);
  });

  test("test_choosing_areas_writes_nothing_to_the_address_storage_or_the_console", async () => {
    const watching = watch();
    try {
      const { user } = show();
      for (const at of [0, 1, 2]) await user.click(add(at));
      await user.click(within(tray()).getByRole("button", { name: TRAY.clear }));

      expect(watching.storage).toEqual([]);
      expect(watching.history).toEqual([]);
      expect(watching.console).toEqual([]);
    } finally {
      watching.stop();
    }
  });

  test("test_what_the_tray_says_of_each_count", () => {
    expect([0, 1, 2, 3].map((count) => trayStatus(count, false))).toEqual([TRAY.none, TRAY.one, "", ""]);
    expect(trayStatus(4, true)).toBe(TRAY.full);
  });
});
