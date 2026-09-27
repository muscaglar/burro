/** @jest-environment node */
/**
 * Where the addresses of the pages of accounts lead while accounts are off: to where no
 * page stands, before any folder of the website is asked.
 *
 * What a built website then answers is seen by asking one: a test reads the rule, and
 * that the settings of the website hold it.
 */

import { existsSync, readdirSync } from "node:fs";
import path from "node:path";

import config from "../../../next.config";
import { ledNowhere, NOWHERE } from "./off";
import { ACCOUNTS_VARIABLE, ON } from "./on";
import { ACCOUNT_PAGES } from "./paths";

const APP = path.resolve(__dirname, "..", "..", "app");

afterEach(() => {
  delete process.env[ACCOUNTS_VARIABLE];
});

describe("with accounts off", () => {
  test("test_the_address_of_every_page_of_accounts_and_whatever_follows_it_is_led_to_where_no_page_stands", () => {
    const led = ledNowhere();

    expect(led).toEqual(
      ["/sign-in", "/sign-in/:rest*", "/account", "/account/:rest*"].map((source) => ({ source, destination: NOWHERE })),
    );
    // Every page of accounts stands at one of them, or under one.
    const roots = led.map((one) => one.source).filter((source) => !source.includes(":"));
    expect(ACCOUNT_PAGES.filter((page) => !roots.some((root) => page === root || page.startsWith(`${root}/`)))).toEqual([]);
  });

  test("test_no_page_stands_where_they_are_led_and_no_folder_takes_an_address_of_one_part", () => {
    expect(NOWHERE).toMatch(/^\/[a-z-]+$/);
    expect(existsSync(path.join(APP, NOWHERE.slice(1)))).toBe(false);
    // A folder that took whatever one part it was given would take this address too,
    // whether a page stood in it or a handler.
    const taking = readdirSync(APP, { withFileTypes: true })
      .filter((entry) => entry.isDirectory() && entry.name.startsWith("["))
      .filter((entry) => ["page.tsx", "route.ts"].some((file) => existsSync(path.join(APP, entry.name, file))));
    expect(taking.map((entry) => entry.name)).toEqual([]);
  });

  test("test_the_settings_of_the_website_hold_the_rule_before_any_folder_is_asked", async () => {
    expect(await config.rewrites?.()).toEqual({ beforeFiles: ledNowhere(), afterFiles: [], fallback: [] });
    expect(ledNowhere()).toHaveLength(4);
  });

  test.each(["", "off", "true", "1", "ON"])("test_they_are_off_unless_the_one_setting_says_on: %s", (value) => {
    process.env[ACCOUNTS_VARIABLE] = value;

    expect(ledNowhere()).toHaveLength(4);
  });
});

describe("with accounts on", () => {
  test("test_no_address_is_led_anywhere", async () => {
    process.env[ACCOUNTS_VARIABLE] = ON;

    expect(ledNowhere()).toEqual([]);
    expect(await config.rewrites?.()).toEqual({ beforeFiles: [], afterFiles: [], fallback: [] });
  });
});
