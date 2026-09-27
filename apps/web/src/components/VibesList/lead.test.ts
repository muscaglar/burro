/** @jest-environment node */
import { VIBES } from "@/content/vibes";
import { readRecorded, recordedAnswer } from "@/lib/api/recorded";
import type { MetaData } from "@/lib/api/schema";

import { leadOf } from "./lead";
import { EXAMPLES } from "./look";

const meta: MetaData = recordedAnswer("get_meta", "meta").body.data;
const variantA: MetaData = (readRecorded("variant-a/meta").body as { data: MetaData }).data;

describe("what the page of vibes is for", () => {
  test("test_it_says_what_a_vibe_is_in_words_a_newcomer_knows_and_what_follows_from_how_one_is_worked_out", () => {
    const lead = leadOf(meta);

    // The founder's own sentences, from the direction on how the words are written.
    expect(lead.startsWith("A vibe is a way of describing what an area feels like, such as ")).toBe(true);
    expect(lead).toContain("which means you can always see what went into it and what it leaves out.");
    expect(/recipe|measured parts|published/.test(lead)).toBe(false);
  });

  test("test_the_two_vibes_it_names_are_vibes_of_the_data_by_the_names_the_api_gives_them", () => {
    expect(EXAMPLES).toBe("named");
    expect(leadOf(meta)).toContain("such as Leafy or Going out.");
    // It names none the data does not hold.
    const few = { ...meta, tags: meta.tags.filter((tag) => ["homes", "foodie", "leafy"].includes(tag.tag_id)) };
    expect(leadOf(few)).toContain("such as Leafy or Houses or flats.");
  });

  test("test_it_names_no_vibe_that_has_more_to_say_of_itself_than_its_name", () => {
    // A vibe that counts recorded crime says that it does, and one the service says is less
    // sure is held back from what is said in short. Neither is named in passing.
    const named = (given: MetaData) => /such as (.+) or (.+)\. Burro works/.exec(leadOf(given))?.slice(1, 3) ?? [];
    const rough = { ...meta, tags: meta.tags.map((tag) => (tag.tag_id === "leafy" ? { ...tag, sureness: "rough_guide" as const } : tag)) };
    const crimeFirst = { ...meta, tags: [...meta.tags.filter((tag) => tag.tag_id === "street_character"), ...meta.tags.filter((tag) => tag.tag_id !== "street_character")] };

    expect(named(meta)).toEqual(["Leafy", "Going out"]);
    expect(named(rough)).toEqual(["Going out", "Quiet streets"]);
    expect(named(crimeFirst)).toEqual(["Leafy", "Going out"]);
    expect(named(variantA)).toEqual(["Leafy", "Going out"]);
  });

  test("test_with_fewer_than_two_vibes_to_name_it_names_none_and_is_a_whole_sentence_still", () => {
    expect(leadOf({ ...meta, tags: [] })).toBe(VIBES.lead());
    expect(leadOf({ ...meta, tags: meta.tags.slice(0, 1) })).toBe(VIBES.lead());
    expect(VIBES.lead()).toMatch(/^A vibe is a way of describing what an area feels like\. Burro works each one out/);
  });

  test("test_asked_to_it_is_the_founders_own_two_examples_as_written", () => {
    expect(leadOf(meta, "written")).toBe(VIBES.leadAsWritten);
    expect(VIBES.leadAsWritten).toContain("such as leafy or well connected.");
  });
});
