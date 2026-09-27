/** @jest-environment node */

import { recordedAnswer } from "@/lib/api/recorded";
import { chipsOf } from "@/lib/search/chips";

import { drawingOf, PLAIN } from "../kit/Thing/drawn";
import { stateOf, thingOf } from "./drawn";

const meta = recordedAnswer("get_meta", "meta").body.data;
const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const first = recordedAnswer("interpret", "interpret-first").body.data;

describe("the thing of a chip", () => {
  test("test_a_vibe_is_drawn_by_the_id_and_the_family_the_service_gives_and_by_nothing_written_here", () => {
    for (const tag of meta.tags) {
      expect(thingOf({ kind: "tag", id: tag.tag_id }, meta)).toEqual({ kind: "tag", id: tag.tag_id, family: tag.family });
    }
    for (const one of meta.features) {
      expect(thingOf({ kind: "feature", id: one.feature_id }, meta)).toEqual({
        kind: "feature",
        id: one.feature_id,
        family: one.family,
      });
    }
  });

  test("test_a_vibe_of_a_later_release_falls_to_the_plain_drawing_and_is_never_drawn_as_nothing", () => {
    const later = thingOf({ kind: "tag", id: "of_a_later_release" }, meta);

    expect(later).toEqual({ kind: "tag", id: "of_a_later_release", family: null });
    expect(drawingOf(later)).toBe(PLAIN);
    expect(drawingOf(thingOf({ kind: "feature", id: "of_a_later_release" }, meta))).toBe(PLAIN);
  });

  test("test_every_other_chip_is_drawn_by_its_kind_and_the_id_of_a_place_is_handed_to_nothing", () => {
    const chips = chipsOf(
      { ...first.spec, areas: [{ area_id: areas[0]?.area_id ?? "", rule: "exclude", provenance: "ui_edit" }] },
      meta,
      areas,
      {},
      {},
    );
    const others = chips.filter((chip) => chip.kind !== "tag" && chip.kind !== "feature");

    expect(others.map((chip) => chip.kind).sort()).toEqual(["area", "budget", "place", "tenure"]);
    // Its kind and nothing else: no id of a place or of an area is among what is drawn.
    expect(others.map((chip) => thingOf(chip, meta))).toEqual(others.map((chip) => ({ kind: chip.kind })));
  });

  test("test_which_journey_counts_is_drawn_as_a_journey_is", () => {
    expect(thingOf({ kind: "journeys", id: null }, meta)).toEqual({ kind: "place" });
  });
});

describe("the state of a chip", () => {
  const [asked] = first.spec.tags;
  const vibe = { kind: "tag", id: asked?.tag_id ?? "" } as const;

  test("test_what_a_person_said_is_said_and_what_nobody_said_the_whole_of_is_assumed", () => {
    expect(stateOf({ ...vibe, assumed: false }, first.spec)).toBe("said");
    expect(stateOf({ ...vibe, assumed: true }, first.spec)).toBe("assumed");
    expect(stateOf({ kind: "tenure", id: null, assumed: true }, first.spec)).toBe("assumed");
    expect(stateOf({ kind: "place", id: first.spec.commutes[0]?.place_id ?? "", assumed: false }, first.spec)).toBe("said");
  });

  test("test_a_weight_of_nought_counts_for_nothing_and_is_drawn_so_whoever_said_it", () => {
    const off = { ...first.spec, tags: first.spec.tags.map((tag) => ({ ...tag, weight: 0 })) };

    expect(stateOf({ ...vibe, assumed: false }, off)).toBe("off");
    expect(stateOf({ ...vibe, assumed: true }, off)).toBe("off");

    const [usual] = first.spec.weights;
    const measure = { kind: "feature", id: usual?.feature_id ?? "", assumed: false } as const;
    expect(stateOf(measure, first.spec)).toBe("said");
    expect(stateOf(measure, { ...first.spec, weights: first.spec.weights.map((one) => ({ ...one, weight: 0 })) })).toBe("off");
  });

  test("test_a_chip_that_stands_for_no_weight_is_never_drawn_as_counting_for_nothing", () => {
    const none = { tags: [], weights: [] };

    for (const kind of ["tenure", "budget", "place", "area", "journeys"] as const) {
      expect([kind, stateOf({ kind, id: null, assumed: false }, none)]).toEqual([kind, "said"]);
    }
    // Nor is a vibe the search does not hold: there is no weight of it to be nought.
    expect(stateOf({ kind: "tag", id: "not_in_the_search", assumed: false }, none)).toBe("said");
  });
});
