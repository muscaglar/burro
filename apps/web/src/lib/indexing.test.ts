/** @jest-environment node */
import { KEEP_OUT, KEEP_OUT_HEADER, keepOutHeaders, mayBeIndexed, siteOrigin, wholeAddress } from "./indexing";

afterEach(() => {
  delete process.env.BURRO_SITE_URL;
});

describe("the website's own address", () => {
  test.each([
    ["https://burro.example", "https://burro.example"],
    ["https://burro.example/", "https://burro.example"],
    ["  https://burro.example  ", "https://burro.example"],
    ["http://localhost:3000", "http://localhost:3000"],
  ])("test_the_address_is_read_as_an_origin: %s", (value, origin) => {
    process.env.BURRO_SITE_URL = value;

    expect(siteOrigin()).toBe(origin);
  });

  test.each([
    "",
    "burro.example",
    "ftp://burro.example",
    "https://burro.example/somewhere",
    "https://burro.example/?page=1",
    "https://burro.example/#part",
    // A placeholder: an address with a name and a password in it is refused.
    "https://name:password@burro.example", // public-only: allow
  ])("test_what_is_not_a_plain_origin_is_no_address: %s", (value) => {
    process.env.BURRO_SITE_URL = value;

    expect(siteOrigin()).toBeNull();
    expect(wholeAddress("/methods")).toBeNull();
  });

  test("test_a_whole_address_is_the_origin_and_a_path_of_the_website", () => {
    process.env.BURRO_SITE_URL = "https://burro.example/";

    expect(wholeAddress("/london/dulcimer-green")).toBe("https://burro.example/london/dulcimer-green");
    // A path that names another host is no path of the website.
    expect(wholeAddress("//elsewhere.example/")).toBeNull();
    expect(wholeAddress("methods")).toBeNull();
  });
});

describe("whether a search engine may index the website", () => {
  test.each([
    [true, "https://burro.example", false],
    [true, undefined, false],
    [false, undefined, false],
    [false, "https://burro.example", true],
  ])("test_only_real_data_at_a_known_address_may_be_indexed: synthetic %s at %s", (synthetic, address, may) => {
    if (address !== undefined) process.env.BURRO_SITE_URL = address;

    expect(mayBeIndexed({ synthetic, preview: false })).toBe(may);
  });

  test.each([true, false])(
    "test_a_preview_is_never_indexed_whether_its_data_is_real_or_made_up: synthetic %s",
    (synthetic) => {
      process.env.BURRO_SITE_URL = "https://burro.example";

      expect(mayBeIndexed({ synthetic, preview: true })).toBe(false);
    },
  );

  test("test_keeping_out_means_neither_indexing_nor_following", () => {
    expect(KEEP_OUT).toEqual({ index: false, follow: false });
    expect(KEEP_OUT_HEADER).toEqual({ key: "X-Robots-Tag", value: "noindex, nofollow" });
  });

  test("test_while_nothing_may_be_indexed_every_answer_carries_the_header", () => {
    expect(keepOutHeaders(false)).toEqual([{ source: "/:path*", headers: [KEEP_OUT_HEADER] }]);
  });

  test("test_once_pages_may_be_indexed_only_the_pages_that_are_one_persons_carry_it", () => {
    expect(keepOutHeaders(true)).toEqual([
      { source: "/compare", headers: [KEEP_OUT_HEADER] },
      { source: "/s", headers: [KEEP_OUT_HEADER] },
    ]);
  });
});
