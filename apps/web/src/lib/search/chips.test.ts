import { recordedAnswer } from "@/lib/api/recorded";

import { CRIME_ACCOUNT } from "@/content/crime";
import { MODE, SEGMENT } from "@/content/labels";
import { CHIPS, PLACE } from "@/content/search";

import { problemsWith } from "../../../test/support/contract";
import { ROUGH, sayingSo } from "../../../test/support/rough";
import { chipsOf, endAskedFor, namesOfPlaces } from "./chips";

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
      { chip: "Leafy", parts: [], assumed: false },
      { chip: "Quiet streets", parts: [], assumed: false },
      {
        chip: "Cindermoor Works",
        parts: ["public transport (assumed)", "35 minutes", "flexible (assumed)"],
        assumed: true,
      },
      {
        chip: "£1,700 a month",
        parts: ["one bedroom", "flexible (assumed)"],
        assumed: true,
      },
      // The sentence said "Renting", so the spec says the tenure was stated.
      { chip: "Renting", parts: [], assumed: false },
    ]);
  });

  test("test_a_part_of_a_chip_follows_a_comma_and_begins_with_a_small_letter", () => {
    // Seen in a browser, on every search that holds a budget or a journey: "£1,700 a month,
    // One bedroom, firm limit" and "Cindermoor Works, Public transport assumed". How a
    // journey is made and the kind of a home are written to begin a line, as they do where
    // they are chosen. In a chip each follows a comma.
    const homes = Object.keys(SEGMENT) as (keyof typeof SEGMENT)[];
    const ways = Object.keys(MODE) as (keyof typeof MODE)[];
    const partsOf = (spec: typeof first.spec) =>
      chipsOf(spec, meta, areas, NAMES, {}).flatMap((chip) => chip.parts.map((part) => part.text));
    const every = [
      ...homes.flatMap((segment) => partsOf({ ...first.spec, budget: { ...first.spec.budget, segment } })),
      ...ways.flatMap((mode) => partsOf({ ...first.spec, commutes: first.spec.commutes.map((one) => ({ ...one, mode })) })),
    ];

    expect(every.filter((part) => /^[A-Z]/.test(part))).toEqual([]);
    expect(every).toEqual(expect.arrayContaining(["one bedroom", "a flat", "a terraced house", "public transport", "by bike", "on foot"]));
    // Where they are chosen they begin a line, and are written as they were.
    expect([SEGMENT.bed_1, MODE.pt]).toEqual(["One bedroom", "Public transport"]);
  });

  test("test_what_was_asked_for_by_way_of_character_comes_first_and_renting_or_buying_last", () => {
    // Seen in a browser: the chips ran tenure, budget, place, and then the vibes. Three were
    // shown, so with a budget and a workplace no vibe was ever seen.
    const spec = {
      ...recordedAnswer("interpret", "interpret-second-sentence").body.data.spec,
      areas: [{ area_id: "syn-n0006", rule: "exclude", provenance: "ui_edit" }],
    } as const;
    const kinds = chipsOf(spec, meta, areas, NAMES, {}).map((chip) => chip.kind);

    expect(new Set(kinds)).toEqual(new Set(["tag", "feature", "place", "budget", "area", "tenure"]));
    // Each kind stands together, and in this order.
    expect(kinds.filter((kind, at) => kind !== kinds[at - 1])).toEqual([
      "tag",
      "feature",
      "place",
      "budget",
      "area",
      "tenure",
    ]);
  });

  test("test_chips_are_drawn_from_the_spec_and_not_from_the_edits", () => {
    // The same spec gives the same chips, whatever edits made it.
    const ranked = recordedAnswer("rank", "rank-first").body.data.spec;

    expect(said(ranked)).toEqual(said(first.spec));
  });

  test("test_before_anything_is_said_there_is_the_tenure_and_no_chip_of_the_settings_nobody_chose", () => {
    expect(said(meta.defaults.rent)).toEqual([
      { chip: "Renting", parts: [], assumed: true },
    ]);
    expect(said(meta.defaults.buy).map((chip) => chip.chip)).toEqual(["Buying"]);
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
    expect(said(switchedOff).find((chip) => chip.chip === "Nearer a station")).toEqual({
      chip: "Nearer a station",
      parts: ["does not count"],
      assumed: false,
    });
    expect(said(switchedOff).at(-1)?.chip).toBe("Renting");
  });

  test("test_a_code_the_website_has_no_word_for_makes_no_empty_part", () => {
    // As a newer API might send. The chip says what it can, and nothing in place of the rest.
    const newer = {
      ...first.spec,
      commutes: first.spec.commutes.map((commute) => ({ ...commute, mode: "boat" })),
    } as unknown as typeof first.spec;

    expect(said(newer).find((chip) => chip.chip === "Cindermoor Works")?.parts).toEqual([
      "35 minutes",
      "flexible",
    ]);
  });

  test("test_a_tenure_the_person_stated_is_not_marked_assumed", () => {
    const buyer = recordedAnswer("interpret", "interpret-buyer-family").body.data.spec;

    expect(buyer.tenure_from).toBe("stated");
    expect(said(buyer).find((chip) => chip.chip === "Buying")).toEqual({ chip: "Buying", parts: [], assumed: false });
    expect(said(buyer).map((chip) => chip.chip)).toContain("£450,000");
  });

  test("test_a_tenure_said_of_the_one_a_search_starts_from_is_not_marked_assumed", () => {
    // Seen in a browser: "Renting assumed" after the person typed "Renting". The API now
    // says the tenure was stated whether or not it moved, and the chip is drawn from that.
    expect(meta.defaults.rent.tenure).toBe("rent");
    expect(first.spec.tenure_from).toBe("stated");

    expect(chipsOf(first.spec, meta, areas, NAMES, {}).find((chip) => chip.kind === "tenure")).toMatchObject({
      label: "Renting",
      assumed: false,
    });
  });

  test("test_a_tenure_picked_before_anything_was_sent_is_not_marked_assumed", () => {
    // The page then shows the default the API served for that tenure, which no edit made.
    const chip = (tenurePicked: boolean) =>
      chipsOf(meta.defaults.buy, meta, areas, {}, {}, { tenurePicked }).find((one) => one.kind === "tenure");

    expect(meta.defaults.buy.tenure_from).toBe("default");
    expect(chip(false)).toMatchObject({ label: "Buying", assumed: true });
    expect(chip(true)).toMatchObject({ label: "Buying", assumed: false });
  });

  test("test_a_wish_read_into_looser_words_is_marked_assumed", () => {
    const river = recordedAnswer("interpret", "interpret-by-the-river").body.data.spec;

    const loose = said(river).filter((chip) => chip.chip.startsWith("Age of buildings") || chip.chip.includes("river"));

    expect(loose).toEqual([
      { chip: "Age of buildings: towards Historic", parts: [], assumed: true },
      { chip: "Nearer a river or canal", parts: [], assumed: true },
    ]);
  });

  test("test_a_chip_of_a_scale_says_which_end_is_asked_for_and_can_be_turned", () => {
    const calm = recordedAnswer("interpret", "interpret-scale").body.data.spec;
    const pace = meta.tags.find((tag) => tag.tag_id === "pace");

    const chip = chipsOf(calm, meta, areas, {}, {}).find((one) => one.id === "pace");

    expect(pace).toMatchObject({ shape: "scale", low_end: "Calm", high_end: "Buzzy" });
    expect(chip?.label).toBe(CHIPS.towards("Going out", "Calm"));
    // Turning it asks for the other end, with the weight it has, in an edit the API takes.
    expect(chip?.turn?.tag_ops).toEqual([
      { action: "set", tag_id: "pace", value: 0.5, step: "none", toward: "high", provenance: "ui_edit" },
    ]);
    expect(problemsWith("Operations", chip?.turn)).toEqual([]);
  });

  test("test_a_chip_of_a_vibe_whose_recipe_holds_recorded_crime_says_so_in_the_row", () => {
    // Recorded crime counts only when a person asks for it. A person who asked for Gritty was
    // ranked on recorded criminal damage, and nothing on the page of results said so.
    const gritty = recordedAnswer("interpret", "interpret-gritty").body.data.spec;
    const chip = chipsOf(gritty, meta, areas, {}, {}).find((one) => one.key === "tag:street_character");

    expect(chip?.label).toBe(CHIPS.towards("Gritty", "Gritty"));
    expect(chip?.parts).toEqual([{ text: CRIME_ACCOUNT.chip, assumed: false, always: true }]);
    expect(chip?.assumed).toBe(false);
    // No other vibe says it, and one that was taken off counts nothing.
    const others = chipsOf(first.spec, meta, areas, NAMES, {}).filter((one) => one.kind === "tag");
    expect(others.flatMap((one) => one.parts)).toEqual([]);
    const off = { ...gritty, tags: gritty.tags.map((tag) => ({ ...tag, weight: 0 })) };
    expect(chipsOf(off, meta, areas, {}, {}).find((one) => one.kind === "tag")?.parts).toEqual([
      { text: CHIPS.off, assumed: false },
    ]);
  });

  test("test_no_chip_says_how_sure_a_vibe_is", () => {
    // The founder had the label go, and what stood beside it: no page passes it on. The
    // service says still which vibe it holds less sure, in a code, and the chip of one is as
    // any other. What it said of the vibe until it stopped a service may say again: so the
    // chips are made of the release as such a service gave it, with both laid on it.
    const told = sayingSo(meta);
    expect(meta.tags.filter((tag) => tag.sureness === "rough_guide").map((tag) => tag.tag_id)).toEqual([ROUGH.tag_id]);
    expect(told.rough_guides).toEqual([ROUGH]);
    const spec = {
      ...first.spec,
      tags: [...first.spec.tags, { tag_id: ROUGH.tag_id, weight: 0.5, toward: "high", provenance: "stated" }],
    } as const;
    const chip = chipsOf(spec, told, areas, NAMES, {}).find((one) => one.key === `tag:${ROUGH.tag_id}`);

    expect(chip).toMatchObject({ label: "Village feel", parts: [], assumed: false });
    const words = chipsOf(spec, told, areas, NAMES, {}).flatMap((one) => [one.label, ...one.parts.map((part) => part.text)]);
    expect(words.filter((word) => /rough|guide|sure/i.test(word))).toEqual([]);
    expect(words.filter((word) => word.includes(ROUGH.label) || word.includes(ROUGH.why))).toEqual([]);
    // Nor does a chip hold either where nothing is drawn of it.
    const held = JSON.stringify(chipsOf(spec, told, areas, NAMES, {}));
    expect([held.includes(ROUGH.label), held.includes(ROUGH.why)]).toEqual([false, false]);
  });

  test("test_a_vibe_that_runs_one_way_has_no_end_to_name_and_nothing_to_turn", () => {
    const leafy = chipsOf(first.spec, meta, areas, NAMES, {}).find((one) => one.id === "leafy");
    const tag = meta.tags.find((one) => one.tag_id === "leafy");

    expect(tag === undefined ? "" : endAskedFor(tag, "high")).toBeNull();
    expect(leafy).toMatchObject({ label: "Leafy", turn: null });
  });

  test("test_a_word_with_two_meanings_is_quoted_on_the_chip_of_what_it_was_read_as", () => {
    // Where gritty is built from land use alone, "gritty" is read as its place part.
    const read = recordedAnswer("interpret", "variant-a/interpret-gritty").body.data;
    const form = recordedAnswer("get_meta", "variant-a/meta").body.data;
    const key = "tag:works_warehouses";

    const quoted = chipsOf(read.spec, form, areas, {}, { [key]: ["weight", "word"] }, { quoted: { [key]: "gritty" } });
    const unquoted = chipsOf(read.spec, form, areas, {}, { [key]: ["weight"] }, { quoted: { [key]: "gritty" } });

    expect(read.assumptions).toContainEqual({ code: "word", group: "tag_ops", index: 0, word: "gritty" });
    expect(quoted.find((chip) => chip.key === key)).toMatchObject({
      label: "Works and warehouses",
      parts: [{ text: CHIPS.readFrom("gritty"), assumed: true }],
      assumed: true,
    });
    // Once the person has set the vibe themselves it is theirs, and the word is no longer said.
    expect(unquoted.find((chip) => chip.key === key)?.parts).toEqual([]);
  });

  test("test_a_feature_that_counts_either_way_says_which_way", () => {
    const nights = recordedAnswer("interpret", "interpret-nights-out").body.data.spec;

    const venues = said(nights, { "feature:venue_evening_per_homes": ["direction"] }).filter((chip) =>
      chip.chip.startsWith("Pubs"),
    );

    // The chip is named by the plain name the API gives the feature.
    expect(venues).toEqual([{ chip: "Pubs and bars", parts: ["more (assumed)"], assumed: true }]);
  });

  test("test_a_place_that_was_taken_for_the_person_says_so_after_its_name_whatever_its_parts_say", () => {
    // A name that several places bear is taken as the first of them. Nobody chose it, and
    // the chip says so of the place itself, and not only of how to travel there.
    const taken = { "place:syn-p0021": ["mode", "strictness", "place"] } as const;
    const chip = (assumed: Parameters<typeof chipsOf>[4]) =>
      chipsOf(first.spec, meta, areas, NAMES, assumed).find((one) => one.kind === "place");

    expect(chip(taken)).toMatchObject({ label: "Cindermoor Works", taken: true, assumed: true });
    expect(chip(taken)?.parts.map((part) => part.assumed)).toEqual([true, false, true]);
    // A place a person named in full, or picked, is theirs, whatever was assumed of the way there.
    expect(chip(ASSUMED)).toMatchObject({ taken: false, assumed: true });
    expect(chip({ "place:syn-p0021": ["place"] })).toMatchObject({ taken: true, assumed: true });
    expect(chip({})).toMatchObject({ taken: false, assumed: false });
  });

  test("test_a_search_for_somewhere_to_stay_says_visiting_and_has_no_chip_of_a_budget_or_a_home", () => {
    // Visiting is a kind of search of its own. It holds no budget, no number of bedrooms
    // and no kind of home, and nothing of any of them is drawn for it.
    const visiting = { ...first.spec, tenure: "visit", tenure_from: "stated" } as const;
    const chips = chipsOf(visiting, meta, areas, NAMES, {});

    expect(chips.find((chip) => chip.kind === "tenure")).toMatchObject({ label: "Visiting", assumed: false, removal: null });
    expect(chips.map((chip) => chip.kind)).not.toContain("budget");
    expect(chips.map((chip) => chip.label).join(" ")).not.toMatch(/£|bedroom|flat|house|a month/i);
    // Everything else of the search is drawn as it is for any other.
    expect(chips.map((chip) => chip.kind)).toEqual(["tag", "tag", "place", "tenure"]);
    // The same search for a home to rent has the chip of its budget, with the home it is for.
    expect(first.spec.budget.amount).not.toBeNull();
    expect(chipsOf(first.spec, meta, areas, NAMES, {}).map((chip) => chip.kind)).toContain("budget");
  });

  test("test_a_place_is_called_by_the_name_the_answer_gave_it_and_never_by_a_number", () => {
    const two = recordedAnswer("interpret", "interpret-two-journeys").body.data;
    const given = Object.fromEntries(two.places.map((place) => [place.place_id, place.name]));

    expect([...namesOfPlaces(two.spec, given).values()]).toEqual(["Foxholt Market", "Wexmoor University"]);
    // An answer names every place of its spec. One that did not is said to have no name.
    expect([...namesOfPlaces(two.spec, {}).values()]).toEqual([PLACE.noName, PLACE.noName]);
    expect(said(two.spec, {}, {}).filter((chip) => /\d/.test(chip.chip) && !chip.chip.startsWith("£"))).toEqual([]);
  });

  test("test_a_rule_for_an_area_that_burro_took_on_a_guess_says_that_it_was_assumed", () => {
    // "Gorsebeck, only" stood over a ranking of one area, with 21 left out, and nothing
    // said that nobody had asked for that. A rule that a person set says nothing of the kind.
    const only = {
      ...first.spec,
      areas: [{ area_id: "syn-n0006", rule: "only", provenance: "ui_edit" }],
    } as const;

    expect(said(only, { "area:syn-n0006": ["rule"] }).find((chip) => chip.chip === "Farrowmere")).toEqual({
      chip: "Farrowmere",
      parts: ["only (assumed)"],
      assumed: true,
    });
    expect(said(only).find((chip) => chip.chip === "Farrowmere")).toEqual({
      chip: "Farrowmere",
      parts: ["only"],
      assumed: false,
    });
    // What is assumed of another area says nothing of this one.
    expect(said(only, { "area:syn-n0007": ["rule"] }).find((chip) => chip.chip === "Farrowmere")?.assumed).toBe(false);
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

    expect(removable.map((chip) => chip.kind)).toEqual(["tag", "tag", "place", "budget"]);
    expect(chips.filter((chip) => chip.removal === null).map((chip) => chip.kind)).toEqual(["tenure"]);
    for (const chip of removable) expect(problemsWith("Operations", chip.removal)).toEqual([]);
    expect(removable[2]?.removal?.commute_ops[0]).toMatchObject({
      action: "remove",
      place_id: "syn-p0021",
    });
  });

  test("test_no_key_of_a_chip_holds_a_name", () => {
    const chips = chipsOf(first.spec, meta, areas, NAMES, {});

    expect(chips.map((chip) => chip.key)).toEqual([
      "tag:leafy",
      "tag:quiet_residential",
      "place:syn-p0021",
      "budget",
      "tenure",
    ]);
  });
});
