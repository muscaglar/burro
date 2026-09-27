/** @jest-environment node */
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { readRecorded, recordedAnswer } from "@/lib/api/recorded";
import type { MetaData } from "@/lib/api/schema";

import { everyRecording, ROUGH, sayingSo, sayingSoAmong } from "../../../test/support/rough";
import { handed } from "./handed";

const meta: MetaData = recordedAnswer("get_meta", "meta").body.data;
const preview: MetaData = recordedAnswer("get_meta", "preview/meta").body.data;
const variantA: MetaData = (readRecorded("variant-a/meta").body as { data: MetaData }).data;

const SRC = path.resolve(__dirname, "..", "..");

/** Every file of the website that is no test, under a folder. */
function filesUnder(folder: string): string[] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((one) => {
    const full = path.join(folder, one.name);
    if (one.isDirectory()) return filesUnder(full);
    return /\.tsx?$/.test(one.name) && !/\.test\.tsx?$|\.d\.ts$/.test(one.name) ? [full] : [];
  });
}

describe("what a page that runs in the browser is handed of a release", () => {
  test("test_the_service_says_nothing_of_a_rough_guide_in_any_recorded_answer_of_a_release_and_serves_the_list_still", () => {
    // Until 2026-09-26 the service gave the label of such a vibe and the sentence that said
    // why, in `rough_guides`. It gives neither now, and serves the list, which holds nothing.
    const releases = everyRecording().filter((one) => one.request.operation_id === "get_meta");

    expect(releases.length).toBeGreaterThan(10);
    for (const { scenario, body } of releases) {
      const { data } = body as { data: MetaData };
      expect([scenario, data.rough_guides]).toEqual([scenario, []]);
      // Which vibe is less sure it says still, of the vibe itself, in a code.
      expect([scenario, data.tags.filter((tag) => tag.sureness === "rough_guide").map((tag) => tag.tag_id)]).toEqual([scenario, [ROUGH.tag_id]]);
    }
    expect(sayingSoAmong(releases)).toEqual([]);
  });

  test("test_a_page_is_handed_no_label_and_no_sentence_of_a_rough_guide", () => {
    // The founder: "remove the concept of rough guide, we don't want to pass this on to a
    // user". No page drew either, and the first page and the page of a shared search were
    // handed both: what a page is handed is written into the page as it is sent.
    for (const recorded of [meta, preview, variantA]) {
      // A service that is older than the website, or later, may say both. So each is handed
      // as it was recorded, and as such a service gave it.
      const said = sayingSo(recorded);
      expect(said.rough_guides).toEqual([ROUGH]);

      for (const given of [recorded, said]) {
        const page = handed(given);
        const sent = JSON.stringify(page);

        expect("rough_guides" in page).toBe(false);
        expect([sent.includes(ROUGH.label), sent.includes(ROUGH.why)]).toEqual([false, false]);
        expect(/rough guide|less sure/i.test(sent)).toBe(false);
      }
    }
  });

  test("test_everything_else_the_service_said_is_handed_as_it_came", () => {
    const given = sayingSo(meta);
    const page = handed(given);
    const { rough_guides: left, ...rest } = given;

    expect(left).toEqual([ROUGH]);
    expect(Object.keys(page)).toEqual(Object.keys(rest));
    for (const [name, said] of Object.entries(rest)) expect([name, (page as Record<string, unknown>)[name] === said]).toEqual([name, true]);
    // What it was handed is as it was.
    expect(given.rough_guides).toBe(left);
  });

  test("test_every_page_that_hands_the_browser_a_release_hands_it_so", () => {
    // A page under `app` that gives a part the whole of route 11 gives it through `handed`.
    const pages = filesUnder(path.join(SRC, "app")).filter((file) => /\bmeta=\{/.test(readFileSync(file, "utf8")));
    const gives = (file: string) => [...readFileSync(file, "utf8").matchAll(/\bmeta=\{([^}]*)\}/g)].map((found) => found[1]);

    expect(pages.map((file) => path.relative(SRC, file)).sort()).toEqual([
      "app/[city]/[area]/page.tsx",
      "app/account/[[...rest]]/page.tsx",
      "app/layout.tsx",
      "app/methods/page.tsx",
      "app/page.tsx",
      "app/s/page.tsx",
      "app/vibes/page.tsx",
    ]);
    // The three whose part runs in the browser. The rest are drawn on the server, which
    // sends what it drew, and the shell is handed what an answer says of itself and no release.
    for (const page of ["app/page.tsx", "app/s/page.tsx", "app/account/[[...rest]]/page.tsx"]) {
      expect([page, gives(path.join(SRC, page))]).toEqual([page, ["handed(meta.data)"]]);
    }
  });

  test("test_no_part_of_the_website_reads_what_a_rough_guide_says_of_itself", () => {
    // The part that drew nothing and the function that gave nothing are gone, with what named them.
    const reads = /rough_guides|\bRoughGuide\b|\bRoughLabel\b|\bRoughNote\b|\broughOf\b|\.rough\b|\brough=\{/;
    const found = filesUnder(SRC)
      .filter((file) => reads.test(readFileSync(file, "utf8").replace(/\/\*[\s\S]*?\*\/|(?<![:"'`])\/\/.*$/gm, "")))
      .map((file) => path.relative(SRC, file));

    // But the file that leaves it out of what a page is handed.
    expect(found.sort()).toEqual(["lib/api/handed.ts"]);
  });
});
