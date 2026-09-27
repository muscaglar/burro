import { hasBegun } from "@/components/SettingsPanel/groups";
import { recordedAnswer } from "@/lib/api/recorded";

import { startsFrom } from "./begins";

const meta = recordedAnswer("get_meta", "meta").body.data;
const gathered = recordedAnswer("rank", "rank-first").body.data.spec;

describe("what the settings are told a search starts from", () => {
  test("test_while_the_second_way_in_gathers_it_is_what_was_gathered_so_that_no_search_is_said_to_have_begun", () => {
    const told = startsFrom(meta, gathered, true);

    expect(hasBegun(gathered, meta)).toBe(true);
    expect(hasBegun(gathered, told)).toBe(false);
    expect(told.defaults[gathered.tenure]).toBe(gathered);
    // The default of the other tenure is the one the API served, and so is all else of the form.
    const other = gathered.tenure === "rent" ? "buy" : "rent";
    expect(told.defaults[other]).toBe(meta.defaults[other]);
    expect({ ...told, defaults: meta.defaults }).toEqual(meta);
  });

  test("test_once_a_search_is_made_the_form_is_the_form_the_api_served", () => {
    expect(startsFrom(meta, gathered, false)).toBe(meta);
    expect(hasBegun(gathered, startsFrom(meta, gathered, false))).toBe(true);
  });

  test("test_a_default_as_served_is_handed_on_as_it_is", () => {
    expect(startsFrom(meta, meta.defaults.rent, true)).toBe(meta);
    expect(startsFrom(meta, meta.defaults.buy, true)).toBe(meta);
  });

  test("test_the_form_the_api_served_is_never_changed", () => {
    const before = JSON.stringify(meta);

    startsFrom(meta, gathered, true);

    expect(JSON.stringify(meta)).toBe(before);
  });
});
