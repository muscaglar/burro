/** @jest-environment node */
import { contentSecurityPolicy, securityHeaders } from "./headers";

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
