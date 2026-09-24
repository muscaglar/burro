import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen, within } from "@testing-library/react";

import { COMPARE_TABLE } from "@/content/compare";
import { recordedAnswer } from "@/lib/api/recorded";

import { faultsIn } from "../../../test/support/axe";
import { isFor, rulesOf } from "../../../test/support/css";
import { CompareTable } from "./CompareTable";

const three = recordedAnswer("compare", "compare-three").body.data;
const STYLES = rulesOf(readFileSync(path.join(__dirname, "CompareTable.module.css"), "utf8"));

describe("the comparison, stacked on a narrow screen", () => {
  test("test_every_part_of_the_table_says_its_role_so_that_it_stays_a_table_when_stacked", () => {
    render(<CompareTable data={three} />);
    const table = screen.getByRole("table", { name: COMPARE_TABLE.caption });

    // Laid out as blocks, a browser may forget that a table is one. Each part that is
    // laid out so says its role again: the two groups of rows were the ones that did not.
    expect(table).toHaveAttribute("role", "table");
    expect([...table.querySelectorAll("thead, tbody")].map((group) => group.getAttribute("role"))).toEqual([
      "rowgroup",
      "rowgroup",
    ]);
    for (const row of table.querySelectorAll("tr")) expect(row).toHaveAttribute("role", "row");
    for (const cell of table.querySelectorAll("td")) expect(cell).toHaveAttribute("role", "cell");
    for (const header of table.querySelectorAll("thead th")) expect(header).toHaveAttribute("role", "columnheader");
    for (const header of table.querySelectorAll("tbody th")) expect(header).toHaveAttribute("role", "rowheader");
  });

  test("test_every_element_that_is_laid_out_as_a_block_is_one_that_says_its_role", () => {
    const stacked = STYLES.filter(
      (rule) => rule.under !== null && rule.sets.get("display") === "block" && rule.selector.startsWith(".table"),
    );
    const elements = stacked.map((rule) => rule.selector.split(/\s+/).pop());

    expect(elements.sort()).toEqual([".table", "caption", "tbody", "td", "th", "tr"]);
    // The headings of the columns are kept for a screen reader, and not drawn.
    expect(STYLES.some((rule) => rule.under !== null && isFor(rule.selector, "head") && rule.sets.has("clip-path"))).toBe(
      true,
    );
  });

  test("test_each_cell_says_whose_it_is_for_the_eye_and_the_column_says_it_to_a_reader", () => {
    render(<CompareTable data={three} />);
    const rows = within(screen.getByRole("table", { name: COMPARE_TABLE.caption })).getAllByRole("row").slice(1);

    for (const row of rows) {
      const whose = [...row.querySelectorAll("td")].map(
        (cell) => cell.querySelector("[aria-hidden='true']")?.textContent,
      );
      expect(whose).toEqual(three.areas.map((area) => area.name));
    }
  });

  test("test_the_comparison_has_no_accessibility_fault", async () => {
    const { container } = render(<CompareTable data={three} />);

    expect(await faultsIn(container)).toEqual([]);
  });
});
