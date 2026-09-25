import { render } from "@testing-library/react";

import { NAMED } from "@/content/area";
import type { Named } from "@/lib/api/schema";

import { BesideName } from "./BesideName";

const drafted: Named = { label: "Quillhaven 001", source_ids: ["synthetic"], state: "draft" };

function said(area: Parameters<typeof BesideName>[0]["area"]): string | null {
  const { container } = render(<BesideName area={area} className="note" />);
  return container.querySelector("p.note")?.textContent ?? null;
}

describe("what is drawn beside the name of an area", () => {
  test("test_a_drafted_name_has_its_label_beside_it_and_says_that_it_is_a_draft", () => {
    expect(said({ name: "Alderwick", borough: "Quillhaven", named: drafted })).toBe(
      `Quillhaven 001${NAMED.between}${NAMED.draft}`,
    );
  });

  test("test_a_name_a_person_has_checked_has_its_label_beside_it_and_no_word_of_a_draft", () => {
    const checked: Named = { ...drafted, state: "checked" };
    expect(said({ name: "Tallowgate", borough: "Quillhaven", named: checked })).toBe("Quillhaven 001");
  });

  test("test_an_area_that_bears_no_name_but_its_label_has_its_borough_beside_it", () => {
    expect(said({ name: "Grapnel Dock", borough: "Quillhaven", named: null })).toBe("Quillhaven");
  });

  test("test_nothing_is_drawn_beside_a_name_that_says_it_all", () => {
    expect(said({ name: "Quillhaven 009", borough: "Quillhaven", named: null })).toBeNull();
  });

  test("test_in_a_table_the_label_alone_is_drawn_because_the_borough_has_its_own_column", () => {
    const area = { name: "Alderwick", borough: "Tallowgate", named: drafted };
    const { container } = render(<BesideName area={area} className="note" labelOnly />);
    expect(container.querySelector("p.note")?.textContent).toBe("Quillhaven 001");
    const unnamed = render(<BesideName area={{ ...area, named: null }} className="none" labelOnly />);
    expect(unnamed.container.querySelector("p.none")).toBeNull();
  });
});
