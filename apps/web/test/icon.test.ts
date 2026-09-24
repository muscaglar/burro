/**
 * The website's icon. With none, every page a browser opens asks for one and
 * is told there is none. It is one small drawing, written by hand, that loads
 * nothing and runs nothing.
 */

import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { themes } from "./support/contrast";

const APP = path.resolve(__dirname, "..", "src", "app");
const ICON = path.join(APP, "icon.svg");
const written = () => readFileSync(ICON, "utf8");
const drawn = () => new DOMParser().parseFromString(written(), "image/svg+xml");

describe("the website's icon", () => {
  test("test_the_website_has_an_icon_where_the_framework_looks_for_one", () => {
    // Next serves `app/icon.svg` and names it in the head of every page.
    expect(existsSync(ICON)).toBe(true);
    expect(readdirSync(APP).filter((name) => /^(icon|favicon|apple-icon)\./.test(name))).toEqual(["icon.svg"]);
  });

  test("test_the_icon_is_a_drawing_that_can_be_read", () => {
    const icon = drawn();

    expect(icon.querySelector("parsererror")).toBeNull();
    expect(icon.documentElement.tagName).toBe("svg");
    expect(icon.documentElement.getAttribute("viewBox")).toBe("0 0 32 32");
    // Small enough to have been written by hand, and to be read by whoever opens it.
    expect(written().length).toBeLessThan(1500);
  });

  test("test_the_icon_loads_nothing_runs_nothing_and_needs_no_font", () => {
    const icon = drawn();
    const everything = [...icon.querySelectorAll("*")];

    expect(everything.map((one) => one.tagName).filter((tag) => /^(script|foreignObject|image|use|a|text|tspan|iframe)$/i.test(tag))).toEqual([]);
    expect(everything.flatMap((one) => [...one.attributes]).filter(({ name }) => /^on|href$/i.test(name))).toEqual([]);
    expect(/url\(|@import|javascript:/i.test(written())).toBe(false);
    // The one address in it is the name of what it is written in. Nothing is fetched from it.
    expect(written().match(/https?:\/\/[^"'\s)]+/g)).toEqual(["http://www.w3.org/2000/svg"]);
  });

  test("test_the_icon_is_drawn_in_the_colours_of_the_page_in_light_and_in_dark", () => {
    const { light, dark } = themes();
    const colours = [...new Set(written().match(/#[0-9a-f]{3,8}\b/gi) ?? [])].sort();

    expect(colours).toEqual(
      [light["--accent"], light["--on-accent"], dark["--accent"], dark["--on-accent"]].sort(),
    );
    expect(written()).toContain("prefers-color-scheme: dark");
  });
});
