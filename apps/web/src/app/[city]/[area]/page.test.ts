/**
 * What the page of an area says of itself before anything of it is drawn: its title. The
 * page itself is held by the tests of the whole website, under test/area.
 */

import { metadata as notFound } from "@/app/not-found";
import { AREA } from "@/content/area";
import { NOT_FOUND, SITE } from "@/content/site";
import { recordedAnswer } from "@/lib/api/recorded";

import { generateMetadata } from "./page";

const areas = recordedAnswer("list_areas", "areas").body.data.areas;
const at = (city: string, area: string) => ({ params: Promise.resolve({ city, area }) });

describe("the title of the page of an area", () => {
  test.each([
    ["synthetic", "no-such-area"],
    ["synthetic", "Alderwick"],
    ["synthetic", "../meta"],
    ["london", "alderwick"],
  ])("test_an_address_the_release_has_no_area_at_has_the_title_of_a_page_that_is_not_found: /%s/%s", async (city, area) => {
    // Seen in a browser: the page said "Page not found" and its title said "Burro", which
    // is the title of the search. Any other address with no page had the title of what it is.
    const told = await generateMetadata(at(city, area));

    expect(told.title).toBe(NOT_FOUND.title);
    expect(told.title).toBe(notFound.title);
    expect(told.title).not.toBe(SITE.name);
    // It says nothing else of itself: no description of an area that is not there, and no address of one.
    expect(Object.keys(told)).toEqual(["title"]);
  });

  test("test_an_area_of_the_release_has_its_own_name_and_its_borough_for_a_title", async () => {
    const [first] = areas;
    if (first === undefined) throw new Error("The recorded release holds no area.");
    const told = await generateMetadata(at("synthetic", first.slug));

    expect(told.title).toBe(AREA.title(first.name, first.borough));
  });
});
