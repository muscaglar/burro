/** @jest-environment node */
/**
 * What turns accounts on, and which file reads which setting. The secret by which the
 * website says who it is is read in one file, which runs on the server alone: nothing
 * that runs in a browser takes anything from it.
 */

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { ACCOUNTS_VARIABLE, accountsOn, ON } from "./on";
import { ADDRESS_VARIABLE, DEVELOPMENT_VARIABLE, SECRET_VARIABLE } from "./pass";

const SRC = path.resolve(__dirname, "..", "..");
const ROOT = path.resolve(SRC, "..");

function filesUnder(folder: string): string[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(folder, entry.name);
    if (entry.isDirectory()) return filesUnder(full);
    return /\.(ts|tsx|mjs|css)$/.test(entry.name) && !/\.test\.tsx?$/.test(entry.name) ? [full] : [];
  });
}

const files = [...filesUnder(SRC), path.join(ROOT, "next.config.ts")];
const written = (file: string) => readFileSync(file, "utf8");
const named = (file: string) => path.relative(ROOT, file);
const readingThe = (variable: string) => files.filter((file) => written(file).includes(`process.env.${variable}`)).map(named).sort();

/** The files that a file takes from, of the website's own, by their place in the source. */
function takenBy(file: string): string[] {
  const from = [...written(file).matchAll(/(?:from|import)\s+["']([^"']+)["']/g)].map((found) => found[1] ?? "");
  return from.flatMap((name) => {
    const base = name.startsWith("@/") ? path.join(SRC, name.slice(2)) : name.startsWith(".") ? path.resolve(path.dirname(file), name) : null;
    if (base === null) return [];
    return [base, `${base}.ts`, `${base}.tsx`, path.join(base, "index.ts")].filter((one) => files.includes(one));
  });
}

afterEach(() => {
  delete process.env.NEXT_PUBLIC_BURRO_ACCOUNTS;
});

describe("what turns accounts on", () => {
  test("test_accounts_are_off_until_the_one_setting_says_on", () => {
    expect(accountsOn()).toBe(false);
    for (const value of ["", "off", "true", "1", "yes", "ON", "On", " on", "on "]) {
      process.env.NEXT_PUBLIC_BURRO_ACCOUNTS = value;
      expect([value, accountsOn()]).toEqual([value, false]);
    }
    process.env.NEXT_PUBLIC_BURRO_ACCOUNTS = ON;
    expect(accountsOn()).toBe(true);
  });

  test("test_each_setting_of_accounts_is_read_in_one_file", () => {
    expect([ACCOUNTS_VARIABLE, SECRET_VARIABLE, ADDRESS_VARIABLE, DEVELOPMENT_VARIABLE]).toEqual([
      "NEXT_PUBLIC_BURRO_ACCOUNTS",
      "BURRO_WEBSITE_SECRET",
      "BURRO_CLIENT_ADDRESS_HEADER",
      "BURRO_ACCOUNTS_DEVELOPMENT",
    ]);
    expect(readingThe(ACCOUNTS_VARIABLE)).toEqual([path.join("src", "lib", "account", "on.ts")]);
    expect(readingThe(SECRET_VARIABLE)).toEqual([path.join("src", "lib", "account", "pass.ts")]);
    expect(readingThe(ADDRESS_VARIABLE)).toEqual([path.join("src", "lib", "account", "pass.ts")]);
    expect(readingThe(DEVELOPMENT_VARIABLE)).toEqual([path.join("src", "lib", "account", "pass.ts")]);
  });

  test("test_the_secret_is_no_setting_that_the_browsers_code_may_hold", () => {
    // Next puts a setting into the browser's code only where its name begins so.
    expect(SECRET_VARIABLE.startsWith("NEXT_PUBLIC_")).toBe(false);
    expect(ADDRESS_VARIABLE.startsWith("NEXT_PUBLIC_")).toBe(false);
    expect(DEVELOPMENT_VARIABLE.startsWith("NEXT_PUBLIC_")).toBe(false);
    // Nothing of the environment is read by its name as a string, which no rule would see.
    const byName = files.filter((file) => /process\.env\s*\[/.test(written(file))).map(named);
    expect(byName).toEqual([]);
  });

  test("test_nothing_that_runs_in_a_browser_takes_from_the_file_that_holds_the_secret", () => {
    const holds = path.join(SRC, "lib", "account", "pass.ts");
    const takers = files.filter((file) => takenBy(file).includes(holds)).map(named).sort();

    // The two routes of the website, which run on the server and are served to nobody.
    expect(takers).toEqual([
      path.join("src", "app", "v1", "auth", "[...path]", "route.ts"),
      path.join("src", "app", "v1", "me", "[[...path]]", "route.ts"),
    ]);
    // And nothing takes from those: a route is what is asked, and is handed to no page.
    const routes = takers.map((taker) => path.join(ROOT, taker));
    expect(files.filter((file) => takenBy(file).some((one) => routes.includes(one))).map(named)).toEqual([]);
    expect(written(holds)).not.toMatch(/["']use client["']/);
  });
});
