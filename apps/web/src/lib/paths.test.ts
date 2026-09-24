/** @jest-environment node */
import { cityOf, isCity } from "./city";
import { readableDate } from "./format";
import { paths } from "./paths";

describe("the addresses the website links to", () => {
  test("test_an_areas_address_is_its_city_and_its_slug", () => {
    expect(paths.area({ area_id: "syn-n0001", slug: "alderwick" })).toBe("/synthetic/alderwick");
    expect(paths.area({ area_id: "lon-n0001", slug: "dulcimer-green" })).toBe(
      "/london/dulcimer-green",
    );
  });

  test("test_a_share_id_is_only_ever_in_the_fragment", () => {
    const address = new URL(paths.share("N6BkBdeSvd7xEk0NJVZNzw"), "https://burro.example");

    expect(address.pathname).toBe("/s");
    expect(address.search).toBe("");
    expect(address.hash).toBe("#N6BkBdeSvd7xEk0NJVZNzw");
  });

  test("test_a_comparison_is_addressed_by_slugs_alone", () => {
    expect(paths.compare(["alderwick", "pellam-cross"])).toBe("/compare?a=alderwick&a=pellam-cross");
  });

  test("test_a_source_is_addressed_by_its_id_on_the_sources_page", () => {
    expect(paths.sources()).toBe("/sources");
    expect(paths.sources("os-open-greenspace")).toBe("/sources#os-open-greenspace");
  });

  test("test_a_vibe_is_addressed_by_its_id_in_the_fragment_of_the_vibes_page", () => {
    const address = new URL(paths.vibes("village_feel"), "https://burro.example");

    expect(paths.vibes()).toBe("/vibes");
    // A browser sends the fragment to no server, so nobody is told which vibe was read.
    expect(address.pathname).toBe("/vibes");
    expect(address.search).toBe("");
    expect(address.hash).toBe("#village_feel");
  });

  test.each([
    () => paths.vibes("leafy and quiet"),
    () => paths.vibes("Leafy"),
    () => paths.vibes("pace?text=quiet"),
    () => paths.area({ area_id: "syn-n0001", slug: "Cindermoor Works" }),
    () => paths.area({ area_id: "syn-n0001", slug: "a/../b" }),
    () => paths.area({ area_id: "xyz-n0001", slug: "alderwick" }),
    () => paths.compare(["alderwick", "leafy and quiet"]),
    () => paths.compare(["alderwick&text=leafy"]),
    () => paths.sources("a source"),
    () => paths.share("not a share id"),
    () => paths.share("syn-p0021"),
  ])("test_nothing_a_person_typed_can_be_made_into_an_address: %#", (build) => {
    expect(build).toThrow(/^Not /);
  });

  test("test_a_refusal_does_not_repeat_what_it_refused", () => {
    const canary = "zqxcanary7431";
    const refusals = [
      () => paths.area({ area_id: "syn-n0001", slug: canary.toUpperCase() }),
      () => paths.compare([`${canary} ${canary}`]),
      () => paths.share(canary),
      () => paths.vibes(`${canary} ${canary}`),
    ].map((build) => {
      try {
        return build();
      } catch (error) {
        return String(error);
      }
    });

    expect(refusals.join(" ").toLowerCase()).not.toContain(canary);
  });
});

describe("a part of the methods page", () => {
  test("test_a_part_of_the_methods_page_is_the_page_and_the_name_of_the_part", () => {
    expect(paths.methods()).toBe("/methods");
    expect(paths.methods("confidence")).toBe("/methods#confidence");
    expect(paths.methods("journeys")).toBe("/methods#journeys");
    expect(paths.methods("words")).toBe("/methods#words");
  });
});

describe("the city of an id", () => {
  test("test_an_id_says_which_city_it_belongs_to", () => {
    expect(cityOf("syn-n0001")).toBe("synthetic");
    expect(cityOf("lon-p0042")).toBe("london");
    expect(cityOf("syn-2026-09-23-01")).toBe("synthetic");
    expect(cityOf("par-n0001")).toBeNull();
    expect(cityOf("")).toBeNull();
  });

  test("test_only_the_two_cities_are_cities", () => {
    expect([isCity("synthetic"), isCity("london"), isCity("syn"), isCity("paris")]).toEqual([
      true,
      true,
      false,
      false,
    ]);
  });
});

describe("a date, written for a person", () => {
  test("test_a_date_is_written_out_and_so_is_each_end_of_a_period", () => {
    expect(readableDate("2026-09-23")).toBe("23 September 2026");
    expect(readableDate("2026-09-23T00:00:00Z")).toBe("23 September 2026");
    // Late in the day in UTC is still that day, wherever the page is built.
    expect(readableDate("2026-09-23T23:59:59Z")).toBe("23 September 2026");
    expect(readableDate("2025")).toBe("2025");
    expect(readableDate("2024-10 to 2026-09")).toBe("October 2024 to September 2026");
    expect(readableDate("2026-13-45")).toBe("2026-13-45");
  });
});
