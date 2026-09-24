import { recordedAnswer } from "@/lib/api/recorded";

import { problemsWith } from "../../../test/support/contract";
import { chipsOf, namesOfPlaces } from "./chips";

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const first = recordedAnswer("interpret", "interpret-first").body.data;

const NAMES: Readonly<Record<string, string>> = { "syn-p0021": "Cindermoor Works" };
const ASSUMED = { budget: ["strictness"], "place:syn-p0021": ["mode", "strictness"] } as const;

function said(spec = first.spec, assumed = {}, names = NAMES) {
  return chipsOf(spec, meta, areas, names, assumed).map((chip) => ({
    chip: chip.label,
    parts: chip.parts.map((part) => (part.assumed ? `${part.text} (assumed)` : part.text)),
    assumed: chip.assumed,
  }));
}

describe("the chips", () => {
  test("test_there_is_a_chip_for_each_thing_the_spec_holds", () => {
    expect(said(first.spec, ASSUMED)).toEqual([
      { chip: "Renting", parts: [], assumed: true },
      {
        chip: "£1,700 a month",
        parts: ["One bedroom", "flexible (assumed)"],
        assumed: true,
      },
      {
        chip: "Cindermoor Works",
        parts: ["Public transport (assumed)", "within 35 minutes", "flexible (assumed)"],
        assumed: true,
      },
      { chip: "Leafy", parts: [], assumed: false },
      { chip: "Quiet residential", parts: [], assumed: false },
      { chip: "Usual settings: 6", parts: [], assumed: true },
    ]);
  });

  test("test_chips_are_drawn_from_the_spec_and_not_from_the_edits", () => {
    // The same spec gives the same chips, whatever edits made it.
    const ranked = recordedAnswer("rank", "rank-first").body.data.spec;

    expect(said(ranked)).toEqual(said(first.spec));
  });

  test("test_before_anything_is_said_there_is_the_tenure_and_the_usual_settings", () => {
    expect(said(meta.defaults.rent)).toEqual([
      { chip: "Renting", parts: [], assumed: true },
      { chip: "Usual settings: 6", parts: [], assumed: true },
    ]);
    expect(said(meta.defaults.buy).map((chip) => chip.chip)).toEqual([
      "Buying",
      "Usual settings: 7",
    ]);
  });

  test("test_a_thing_a_person_took_off_is_said_to_count_for_nothing_and_never_shown_as_a_wish", () => {
    // Recorded: "a bit more green space, and ignore the high street". The API keeps an
    // entry of 0 for the high street, so that a change of tenure does not bring it back.
    const second = recordedAnswer("interpret", "interpret-second-sentence").body.data.spec;
    const entry = second.weights.find((weight) => weight.feature_id === "highstreet_access");
    expect(entry).toMatchObject({ weight: 0, provenance: "stated" });

    const chips = chipsOf(second, meta, areas, NAMES, {});
    const highStreet = chips.find((chip) => chip.id === "highstreet_access");
    const green = chips.find((chip) => chip.id === "green_cover");

    expect(highStreet?.parts).toEqual([{ text: "does not count", assumed: false }]);
    // There is nothing left of it to take out.
    expect(highStreet?.removal).toBeNull();
    // What was asked for is as it was: no such words, and it can be taken out.
    expect(green?.parts).toEqual([]);
    expect(green?.removal).not.toBeNull();
    // A usual setting that was switched off by a control is the same.
    const switchedOff = recordedAnswer("rank", "rank-switched-off").body.data.spec;
    expect(said(switchedOff).find((chip) => chip.chip === "Walk to the nearest station")).toEqual({
      chip: "Walk to the nearest station",
      parts: ["does not count"],
      assumed: false,
    });
    expect(said(switchedOff).at(-1)?.chip).toBe("Usual settings: 5");
  });

  test("test_a_code_the_website_has_no_word_for_makes_no_empty_part", () => {
    // As a newer API might send. The chip says what it can, and nothing in place of the rest.
    const newer = {
      ...first.spec,
      commutes: first.spec.commutes.map((commute) => ({ ...commute, mode: "boat" })),
    } as unknown as typeof first.spec;

    expect(said(newer).find((chip) => chip.chip === "Cindermoor Works")?.parts).toEqual([
      "within 35 minutes",
      "flexible",
    ]);
  });

  test("test_a_tenure_the_person_stated_is_not_marked_assumed", () => {
    const buyer = recordedAnswer("interpret", "interpret-buyer-family").body.data.spec;

    expect(buyer.tenure_from).toBe("stated");
    expect(said(buyer)[0]).toEqual({ chip: "Buying", parts: [], assumed: false });
    expect(said(buyer)[1]?.chip).toBe("£450,000");
  });

  test("test_a_tenure_the_person_said_is_not_marked_assumed_though_the_spec_calls_it_a_default", () => {
    // Seen in a browser: "Renting assumed" after the person typed "Renting". Said of the
    // tenure a search starts from, it changes nothing, and the API leaves it marked a default.
    expect(first.spec.tenure_from).toBe("default");
    const chip = (tenure: boolean) =>
      chipsOf(first.spec, meta, areas, NAMES, {}, { tenure }).find((one) => one.kind === "tenure");

    expect(chip(false)).toMatchObject({ label: "Renting", assumed: true });
    expect(chip(true)).toMatchObject({ label: "Renting", assumed: false });
  });

  test("test_a_wish_read_into_looser_words_is_marked_assumed", () => {
    const river = recordedAnswer("interpret", "interpret-by-the-river").body.data.spec;

    const tags = said(river).filter((chip) => ["Historic character", "Waterside"].includes(chip.chip));

    expect(tags).toEqual([
      { chip: "Historic character", parts: [], assumed: true },
      { chip: "Waterside", parts: [], assumed: true },
    ]);
  });

  test("test_a_feature_that_counts_either_way_says_which_way", () => {
    const nights = recordedAnswer("interpret", "interpret-nights-out").body.data.spec;

    const venues = said(nights, { "feature:venue_evening": ["direction"] }).filter((chip) =>
      chip.chip.startsWith("Pubs"),
    );

    expect(venues).toEqual([
      { chip: "Pubs, bars and evening venues", parts: ["more (assumed)"], assumed: true },
    ]);
  });

  test("test_a_place_with_no_name_in_hand_is_called_by_its_position", () => {
    const two = recordedAnswer("interpret", "interpret-two-journeys").body.data.spec;

    const names = namesOfPlaces(two, { "syn-p0026": "Wexmoor University" });

    expect([...names.values()]).toEqual(["Place 1", "Wexmoor University"]);
    expect(said(two, {}, {}).filter((chip) => chip.chip.startsWith("Place"))).toHaveLength(2);
  });

  test("test_a_hidden_area_has_a_chip_with_its_name", () => {
    const hidden = {
      ...first.spec,
      areas: [{ area_id: "syn-n0006", rule: "exclude", provenance: "ui_edit" }],
    } as const;

    expect(said(hidden).find((chip) => chip.chip === "Farrowmere")).toEqual({
      chip: "Farrowmere",
      parts: ["hidden"],
      assumed: false,
    });
  });

  test("test_a_chip_can_be_removed_where_the_setting_can_be_and_the_edit_is_one_the_api_takes", () => {
    const chips = chipsOf(first.spec, meta, areas, NAMES, {});

    const removable = chips.filter((chip) => chip.removal !== null);

    expect(removable.map((chip) => chip.kind)).toEqual(["budget", "place", "tag", "tag"]);
    expect(chips.filter((chip) => chip.removal === null).map((chip) => chip.kind)).toEqual([
      "tenure",
      "usual",
    ]);
    for (const chip of removable) expect(problemsWith("Operations", chip.removal)).toEqual([]);
    expect(removable[1]?.removal?.commute_ops[0]).toMatchObject({
      action: "remove",
      place_id: "syn-p0021",
    });
  });

  test("test_no_key_of_a_chip_holds_a_name", () => {
    const chips = chipsOf(first.spec, meta, areas, NAMES, {});

    expect(chips.map((chip) => chip.key)).toEqual([
      "tenure",
      "budget",
      "place:syn-p0021",
      "tag:leafy",
      "tag:quiet_residential",
      "usual",
    ]);
  });
});
