import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CLARIFY } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";
import type { Clarify } from "@/lib/api/schema";

import { standInApi } from "../../../test/support/api";
import { faultsIn } from "../../../test/support/axe";
import { ClarifyQuestion } from "./ClarifyQuestion";

const [asked] = recordedAnswer("interpret", "interpret-clarify").body.data.clarify;
const [unknown] = recordedAnswer("interpret", "interpret-clarify-no-options").body.data.clarify;
if (!asked || !unknown) throw new Error("the recordings hold no question");

function show(clarify: Clarify, position?: { at: number; of: number }) {
  const api = standInApi().on("search_places", "places-search");
  const told = { onPick: jest.fn(), onLeaveOut: jest.fn() };
  const view = render(
    <ClarifyQuestion
      clarify={clarify}
      search={(text, signal) => api.client.searchPlaces({ q: text, limit: 8 }, signal)}
      position={position}
      {...told}
    />,
  );
  return { api, ...told, user: userEvent.setup({ delay: null }), ...view };
}

describe("the one question Burro asks", () => {
  test("test_it_offers_up_to_five_places_each_by_name_and_kind_then_a_search_then_leave_it_out", () => {
    show(asked);

    const question = screen.getByRole("region", { name: CLARIFY.question });
    const controls = [...question.querySelectorAll("button, input")].map(
      (control) => control.textContent || control.getAttribute("role"),
    );
    expect(controls).toEqual([
      "Pellam CrossStation",
      "Pellam ExchangeDistrict",
      "Pellam InfirmaryHospital",
      "combobox",
      CLARIFY.leaveOut,
    ]);
    expect(asked.options.length).toBeLessThanOrEqual(5);
  });

  test("test_picking_a_place_hands_over_its_id_and_its_name", async () => {
    const { user, onPick } = show(asked);

    await user.click(screen.getByRole("button", { name: /^Pellam Infirmary/ }));

    expect(onPick).toHaveBeenCalledWith(asked.options[2]);
  });

  test("test_with_no_options_there_is_the_search_field_alone_and_it_picks_a_place_the_same_way", async () => {
    const { user, onPick } = show(unknown);

    expect(screen.getByText(CLARIFY.none)).toBeInTheDocument();
    expect(screen.getAllByRole("button").map((button) => button.textContent)).toEqual([CLARIFY.leaveOut]);
    await user.type(screen.getByRole("combobox", { name: CLARIFY.search }), "pel");
    await user.click(await screen.findByRole("option", { name: /^Pellam Exchange/ }));

    expect(onPick).toHaveBeenCalledWith({ id: "syn-p0017", name: "Pellam Exchange" });
  });

  test("test_leave_it_out_is_always_there", async () => {
    const { user, onLeaveOut, onPick } = show(asked);

    await user.click(screen.getByRole("button", { name: CLARIFY.leaveOut }));

    expect(onLeaveOut).toHaveBeenCalledTimes(1);
    expect(onPick).not.toHaveBeenCalled();
  });

  test("test_a_question_about_an_area_offers_areas_and_no_search_for_a_place", () => {
    show({
      group: "area_ops",
      index: 0,
      options: [
        { id: "syn-n0003", name: "Cindermoor", kind: "area" },
        { id: "syn-n0006", name: "Farrowmere", kind: "area" },
      ],
    });

    const question = within(screen.getByRole("region", { name: CLARIFY.questionArea }));
    expect(question.getAllByRole("button").map((button) => button.textContent)).toEqual([
      "CindermoorArea",
      "FarrowmereArea",
      CLARIFY.leaveOut,
    ]);
    expect(question.queryByRole("combobox")).toBeNull();
  });

  test("test_two_questions_are_told_apart_by_their_number", () => {
    show(asked, { at: 1, of: 2 });
    show(unknown, { at: 2, of: 2 });

    expect(screen.getAllByRole("region").map((region) => region.getAttribute("aria-labelledby"))).toHaveLength(2);
    expect(screen.getByRole("region", { name: `${CLARIFY.question} Question 1 of 2.` })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: `${CLARIFY.question} Question 2 of 2.` })).toBeInTheDocument();
  });

  test("test_the_question_has_nowhere_to_hold_what_was_typed", () => {
    // A question is a group, an index and options from the release. The API sends no words back.
    expect(Object.keys(asked).sort()).toEqual(["group", "index", "options"]);
    expect(asked.options.every((option) => Object.keys(option).sort().join() === "id,kind,name")).toBe(true);
  });

  test("test_the_question_has_no_accessibility_fault", async () => {
    const { container } = show(asked);

    expect(await faultsIn(container)).toEqual([]);
  });
});
