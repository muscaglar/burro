/** @jest-environment node */
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { SITE_URL_VARIABLE } from "../indexing";
import { API_URL_VARIABLE, apiBaseUrl, apiOrigin, cleanBaseUrl } from "./config";

const ROOT = path.resolve(__dirname, "..", "..", "..");

function sourceFiles(folder: string): string[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(folder, entry.name);
    if (entry.isDirectory()) return sourceFiles(full);
    return /\.(ts|tsx|mjs)$/.test(entry.name) && !/\.test\.tsx?$/.test(entry.name) ? [full] : [];
  });
}

afterEach(() => {
  delete process.env.NEXT_PUBLIC_BURRO_API_URL;
});

describe("where the API is", () => {
  test.each([
    ["https://api.example.test", "https://api.example.test"],
    ["https://api.example.test/", "https://api.example.test"],
    ["  http://localhost:8000  ", "http://localhost:8000"],
    ["https://example.test/burro/", "https://example.test/burro"],
  ])("test_an_address_is_read_with_no_slash_at_the_end: %s", (value, expected) => {
    expect(cleanBaseUrl(value)).toBe(expected);
  });

  test.each([
    undefined,
    "",
    "   ",
    "api.example.test",
    "ftp://api.example.test",
    "javascript:alert(1)",
    // A placeholder: an address with a name and a password in it is refused.
    "https://name:password@api.example.test", // public-only: allow
    "https://api.example.test/?key=value",
    "https://api.example.test/#part",
  ])("test_what_is_not_a_plain_web_address_is_no_address: %s", (value) => {
    expect(cleanBaseUrl(value)).toBeNull();
  });

  test("test_the_address_is_read_when_it_is_asked_for_and_not_before", () => {
    expect(apiBaseUrl()).toBeNull();
    process.env.NEXT_PUBLIC_BURRO_API_URL = "https://api.example.test/";
    expect(apiBaseUrl()).toBe("https://api.example.test");
  });

  test("test_the_origin_is_the_address_without_its_path", () => {
    expect(apiOrigin("https://example.test:8443/burro/")).toBe("https://example.test:8443");
    expect(apiOrigin(undefined)).toBeNull();
  });

  test("test_one_environment_variable_names_the_api_and_two_files_read_it", () => {
    const files = [...sourceFiles(path.join(ROOT, "src")), path.join(ROOT, "next.config.ts")];
    const readingThe = (variable: string) =>
      files
        .filter((file) => readFileSync(file, "utf8").includes(`process.env.${variable}`))
        .map((file) => path.relative(ROOT, file))
        .sort();
    const named = new Set(
      files.flatMap((file) => readFileSync(file, "utf8").match(/process\.env\.([A-Z0-9_]+)/g) ?? []),
    );

    expect(API_URL_VARIABLE).toBe("NEXT_PUBLIC_BURRO_API_URL");
    // The client's settings, and the content security policy that must name the same origin.
    expect(readingThe(API_URL_VARIABLE)).toEqual([
      "next.config.ts",
      path.join("src", "lib", "api", "config.ts"),
    ]);
    // The website's own address is another matter, read in one file, on the server, and
    // never by the browser: it says where a page lives, and nothing of where the API is.
    expect(SITE_URL_VARIABLE).toBe("BURRO_SITE_URL");
    expect(readingThe(SITE_URL_VARIABLE)).toEqual([path.join("src", "lib", "indexing.ts")]);
    expect([...named].sort()).toEqual([
      "process.env.BURRO_SITE_URL",
      "process.env.NEXT_PUBLIC_BURRO_API_URL",
      "process.env.NODE_ENV",
    ]);
  });
});
