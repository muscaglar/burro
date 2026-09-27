/** @jest-environment node */
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { contentSecurityPolicy, FACES, keptByABrowser, securityHeaders } from "./headers";

function directives(policy: string): Map<string, string[]> {
  return new Map(
    policy.split("; ").map((directive) => {
      const [name, ...values] = directive.split(" ");
      return [name ?? "", values];
    }),
  );
}

/** A value that names somewhere a thing may come from, as against a keyword or a scheme. */
function origins(policy: string): string[] {
  return [...directives(policy).values()].flat().filter((value) => /^[a-z]+:\/\//.test(value));
}

describe("the content security policy", () => {
  test("test_nothing_may_be_loaded_from_another_origin", () => {
    const policy = contentSecurityPolicy("https://api.example.test");

    expect(origins(policy)).toEqual(["https://api.example.test"]);
    expect(directives(policy).get("connect-src")).toEqual(["'self'", "https://api.example.test"]);
    expect(directives(policy).get("default-src")).toEqual(["'self'"]);
    expect(policy).not.toContain("*");
  });

  test("test_a_face_is_fetched_from_the_websites_own_origin_and_is_never_made_by_the_page", () => {
    for (const api of ["https://api.example.test", null]) {
      expect(directives(contentSecurityPolicy(api)).get("font-src")).toEqual(["'self'"]);
    }
  });

  test("test_a_picture_is_the_websites_own_or_one_the_page_made_itself", () => {
    // A drawing is a file under /art/. What the map draws it makes itself, which names no origin.
    for (const api of ["https://api.example.test", null]) {
      expect(directives(contentSecurityPolicy(api)).get("img-src")).toEqual(["'self'", "data:", "blob:"]);
    }
  });

  test("test_the_api_is_asked_for_answers_and_for_nothing_that_is_drawn_or_run", () => {
    // The one other origin is named where the page asks for an answer, and nowhere else: no
    // script, style, face or picture of its may be loaded.
    const policy = directives(contentSecurityPolicy("https://api.example.test"));
    const naming = [...policy].filter(([, values]) => values.includes("https://api.example.test")).map(([name]) => name);

    expect(naming).toEqual(["connect-src"]);
  });

  test("test_with_no_api_set_only_the_websites_own_origin_is_allowed", () => {
    const policy = contentSecurityPolicy(null);

    expect(origins(policy)).toEqual([]);
    expect(directives(policy).get("connect-src")).toEqual(["'self'"]);
  });

  test("test_the_page_cannot_be_framed_or_post_a_form_elsewhere", () => {
    const policy = directives(contentSecurityPolicy("https://api.example.test"));

    expect(policy.get("frame-ancestors")).toEqual(["'none'"]);
    expect(policy.get("form-action")).toEqual(["'self'"]);
    expect(policy.get("base-uri")).toEqual(["'self'"]);
    expect(policy.get("object-src")).toEqual(["'none'"]);
  });

  test("test_scripts_may_be_evaluated_only_while_developing", () => {
    expect(contentSecurityPolicy(null)).not.toContain("unsafe-eval");
    expect(contentSecurityPolicy(null, true)).toContain("'unsafe-eval'");
  });

  test("test_no_site_is_told_which_page_a_person_came_from", () => {
    const headers = new Map(securityHeaders(null).map(({ key, value }) => [key, value]));

    expect(headers.get("Referrer-Policy")).toBe("no-referrer");
    expect(headers.get("X-Content-Type-Options")).toBe("nosniff");
    expect(headers.get("Content-Security-Policy")).toBe(contentSecurityPolicy(null));
  });
});

describe("what a browser may keep", () => {
  const FOLDER = path.resolve(__dirname, "..", "..", "public", "fonts");
  const inFolder = readdirSync(FOLDER).sort();
  const kept = keptByABrowser(inFolder);

  test("test_a_face_is_kept_for_a_year_and_is_not_asked_for_again", () => {
    expect(FACES).toBe("/fonts");
    expect(kept.length).toBeGreaterThan(0);
    for (const { headers } of kept) {
      // Nothing but how long it is kept is said of a file: the policy is said of every answer.
      expect(headers).toEqual([{ key: "Cache-Control", value: "public, max-age=31536000, immutable" }]);
    }
  });

  test("test_only_a_face_that_is_there_is_kept_so_that_a_browser_never_keeps_that_one_is_not", () => {
    // Seen when the website was served: said of every path under /fonts/, a face that was not
    // there was answered "not found, and keep that for a year".
    const faces = inFolder.filter((name) => name.endsWith(".woff2"));

    expect(kept.map(({ source }) => source)).toEqual(faces.map((name) => `/fonts/${name}`));
    // Each is a path and no pattern, and a licence, which may be put right, is not kept.
    expect(kept.filter(({ source }) => /[:*(?+\\]/.test(source))).toEqual([]);
    expect(inFolder.length).toBeGreaterThan(faces.length);
    expect(keptByABrowser(["none.txt", "../next.config.ts", "a face.woff2", ":file*.woff2"])).toEqual([]);
  });

  test("test_every_face_that_is_kept_is_one_the_style_sheet_declares", () => {
    const declared = readFileSync(path.resolve(__dirname, "..", "styles", "base.css"), "utf8");

    for (const { source } of kept) expect(declared).toContain(`url("${source}")`);
  });
});
