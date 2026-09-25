import type { Named } from "@/lib/api/schema";

import { NAMED } from "@/content/area";

import { besideTheName, isDraft, saidOfTheName, saysItsBorough } from "./named";

const drafted: Named = { label: "Quillhaven 001", source_ids: ["synthetic"], state: "draft" };

describe("what stands beside the name of an area", () => {
  test("test_a_name_that_begins_with_its_borough_says_it_already", () => {
    expect(saysItsBorough({ name: "Quillhaven 003", borough: "Quillhaven" })).toBe(true);
    expect(saysItsBorough({ name: "Quillhaven", borough: "Quillhaven" })).toBe(true);
    expect(saysItsBorough({ name: "Alderwick", borough: "Quillhaven" })).toBe(false);
    expect(saysItsBorough({ name: "Alderwick", borough: "" })).toBe(false);
  });

  test("test_the_label_of_a_named_area_stands_beside_its_name_and_says_the_borough_once", () => {
    const named = { name: "Alderwick", borough: "Quillhaven", named: drafted };
    expect(besideTheName(named)).toEqual(["Quillhaven 001"]);
    // A label that does not begin with the borough leaves the borough to be said.
    expect(besideTheName({ ...named, borough: "Tallowgate" })).toEqual(["Tallowgate", "Quillhaven 001"]);
  });

  test("test_an_area_that_bears_no_name_but_its_label_says_its_borough_and_nothing_made_up", () => {
    expect(besideTheName({ name: "Alderwick", borough: "Quillhaven", named: null })).toEqual(["Quillhaven"]);
    expect(besideTheName({ name: "Alderwick", borough: "Quillhaven" })).toEqual(["Quillhaven"]);
    expect(besideTheName({ name: "Quillhaven 001", borough: "Quillhaven", named: null })).toEqual([]);
    expect(besideTheName({ name: "Alderwick", borough: "", named: null })).toEqual([]);
  });

  test("test_what_is_said_of_a_name_is_who_wrote_it_and_whether_a_person_has_checked_it", () => {
    const slots = { name: "Alderwick", borough: "Quillhaven", label: "Quillhaven 001", written_by: "Burro" };
    expect(saidOfTheName({ slots: { ...slots, state: "draft" } })).toBe(NAMED.state.draft("Burro"));
    expect(saidOfTheName({ slots: { ...slots, state: "checked" } })).toBe(NAMED.state.checked("Burro"));
    expect(NAMED.state.draft("Burro")).toContain("No person has checked it");
    // An area that bears no name but its label says nothing of one.
    expect(saidOfTheName({ slots: { name: "Grapnel Dock", borough: "Quillhaven" } })).toBeNull();
    // A state the page has no words for is left out, and never shown as its code.
    expect(saidOfTheName({ slots: { ...slots, state: "approved" } })).toBeNull();
  });

  test("test_a_name_is_a_draft_until_the_api_says_a_person_has_checked_it", () => {
    expect(isDraft({ named: drafted })).toBe(true);
    expect(isDraft({ named: { ...drafted, state: "checked" } })).toBe(false);
    expect(isDraft({ named: null })).toBe(false);
    expect(isDraft({})).toBe(false);
  });
});
