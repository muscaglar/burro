import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";

import { faultsIn } from "../../../test/support/axe";
import { Tabs } from "./Tabs";

type View = "list" | "map" | "table";

function Held() {
  const [view, setView] = useState<View>("list");
  return (
    <>
      <Tabs<View>
        label="Show the results as"
        selected={view}
        onSelect={setView}
        tabs={[
          { id: "list", label: "List", panel: "panel-list" },
          { id: "map", label: "Map", panel: "panel-map" },
          { id: "table", label: "Table", panel: "panel-table" },
        ]}
      />
      {(["list", "map", "table"] as const).map((id) => (
        <div key={id} id={`panel-${id}`} role="tabpanel" aria-label={id} hidden={view !== id}>
          {id}
        </div>
      ))}
    </>
  );
}

const tab = (name: string) => screen.getByRole("tab", { name });
const user = () => userEvent.setup({ delay: null });

describe("a row of tabs", () => {
  test("test_one_tab_is_chosen_at_a_time_and_says_so", async () => {
    render(<Held />);
    expect(screen.getAllByRole("tab").map((one) => one.getAttribute("aria-selected"))).toEqual(["true", "false", "false"]);

    await user().click(tab("Map"));

    expect(screen.getAllByRole("tab").map((one) => one.getAttribute("aria-selected"))).toEqual(["false", "true", "false"]);
    expect(screen.getByRole("tabpanel")).toHaveTextContent("map");
  });

  test("test_every_tab_can_be_reached_with_tab_and_chosen_with_enter_or_space", async () => {
    render(<Held />);
    const press = user();

    await press.tab();
    expect(tab("List")).toHaveFocus();
    await press.tab();
    expect(tab("Map")).toHaveFocus();
    await press.keyboard("{Enter}");
    expect(tab("Map")).toHaveAttribute("aria-selected", "true");
    await press.tab();
    await press.keyboard(" ");
    expect(tab("Table")).toHaveAttribute("aria-selected", "true");
  });

  test("test_the_arrow_keys_home_and_end_move_between_tabs_and_go_round", async () => {
    render(<Held />);
    const press = user();
    await press.click(tab("List"));

    await press.keyboard("{ArrowLeft}");
    expect(tab("Table")).toHaveAttribute("aria-selected", "true");
    expect(tab("Table")).toHaveFocus();
    await press.keyboard("{ArrowRight}");
    expect(tab("List")).toHaveAttribute("aria-selected", "true");
    await press.keyboard("{End}");
    expect(tab("Table")).toHaveFocus();
    await press.keyboard("{Home}");
    expect(tab("List")).toHaveFocus();
  });

  test("test_each_tab_names_the_panel_it_shows_and_takes_a_target_size", () => {
    render(<Held />);

    for (const one of screen.getAllByRole("tab")) {
      expect(document.getElementById(one.getAttribute("aria-controls") ?? "")).not.toBeNull();
      expect(one).toHaveClass("target");
      expect(one).not.toHaveAttribute("tabindex", "-1");
    }
    expect(screen.getByRole("tablist", { name: "Show the results as" })).toBeInTheDocument();
  });

  test("test_the_tabs_have_no_accessibility_fault", async () => {
    const { container } = render(<Held />);

    expect(await faultsIn(container)).toEqual([]);
  });
});
