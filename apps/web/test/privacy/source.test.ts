/** @jest-environment node */
/**
 * What the source itself may and may not hold. These read the files of the
 * website, so they hold whatever is written next as well as what is there now.
 */

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { EXAMPLES } from "@/content/search";
import { readRecorded } from "@/lib/api/recorded";
import type { AreasData, MetaData } from "@/lib/api/schema";
import { contentSecurityPolicy } from "@/lib/headers";

const SRC = path.resolve(__dirname, "..", "..", "src");

function filesUnder(folder: string, found: string[] = []): string[] {
  for (const entry of readdirSync(folder, { withFileTypes: true })) {
    const file = path.join(folder, entry.name);
    if (entry.isDirectory()) filesUnder(file, found);
    else found.push(file);
  }
  return found;
}

const files = filesUnder(SRC);
const source = files.filter((file) => /\.(ts|tsx|css)$/.test(file) && !/\.test\.tsx?$/.test(file));
const written = (file: string) => readFileSync(file, "utf8");
const named = (file: string) => path.relative(SRC, file);
/** The code of a file, with what is said in comments taken out. */
const code = (file: string) => written(file).replace(/\/\*[\s\S]*?\*\/|(?<![:"'`])\/\/.*$/gm, "");

/**
 * The one address the source may name. It is the name of the vocabulary that
 * an area's structured data is written in. It is a name and not a place to
 * fetch from: no browser asks it for anything, and no page links to it.
 */
const VOCABULARY = { file: path.join("lib", "area", "describe.ts"), address: "https://schema.org" };

/**
 * Every provider of a model the service can tell of, and the company of each, read from
 * the contract and from the recorded answers. None is written here.
 */
function providers(): string[] {
  const contract = JSON.parse(
    readFileSync(path.resolve(SRC, "..", "..", "..", "contracts", "openapi.json"), "utf8"),
  ) as { components: { schemas: { Provider: { enum: string[] } } } };
  const told = ["meta-model-reads", "meta-model-reads-with-settings"].map(
    (recorded) => (readRecorded(recorded).body as { data: MetaData }).data.reader,
  );
  const names = [...contract.components.schemas.Provider.enum, ...told.map((reader) => reader.company)];
  return [...new Set(names.filter((name): name is string => typeof name === "string"))];
}

describe("what the source holds", () => {
  test("test_no_providers_name_or_terms_is_written_in_the_websites_own_source", () => {
    // What people are told of a provider is served by the API, from one table, and the
    // website shows it as served. The generated types quote the contract, which lists the
    // providers the service can name, so they are left out: nothing in them is shown.
    const own = source.filter((file) => !file.endsWith("schema.d.ts") && !file.endsWith("required.ts"));
    const names = providers();
    const word = (name: string) => new RegExp(`\\b${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i");
    const naming = own.flatMap((file) =>
      names.filter((name) => word(name).test(written(file))).map((name) => `${named(file)} ${name}`),
    );
    const terms = /\b\d+ (days?|years?)\b[^\n]{0,40}\b(kept|keep|flagged|retain)|\b(kept|keeps?|retains?)\b[^\n]{0,40}\b\d+ (days?|years?)\b/i;

    expect(names.length).toBeGreaterThanOrEqual(4);
    expect(own.length).toBeGreaterThan(80);
    expect(naming).toEqual([]);
    expect(own.filter((file) => terms.test(code(file))).map(named)).toEqual([]);
  });


  test("test_nothing_is_loaded_from_another_origin", () => {
    const anAddress = /\b(https?:)?\/\/[a-z0-9-]+(\.[a-z0-9-]+)+/gi;
    // The generated types quote the contract, which names no address either.
    const naming = source
      .filter((file) => !file.endsWith("schema.d.ts"))
      .flatMap((file) => (code(file).match(anAddress) ?? []).map((address) => `${named(file)} ${address}`));

    expect(source.length).toBeGreaterThan(80);
    expect(naming).toEqual([`${VOCABULARY.file} ${VOCABULARY.address}`]);
    expect(source.filter((file) => /@import|url\(\s*["']?(https?:)?\/\//.test(code(file))).map(named)).toEqual([]);
    // The policy names the website's own origin and the API's, and no other.
    const policy = contentSecurityPolicy("https://api.example.test");
    const origins = new Set(policy.match(/https?:\/\/[^\s;]+/g));
    expect([...origins]).toEqual(["https://api.example.test"]);
    expect(/(^|[\s;])\*([\s;]|$)/.test(policy)).toBe(false);
  });

  test("test_the_website_has_no_handler_action_or_middleware", () => {
    const app = files.filter((file) => file.startsWith(path.join(SRC, "app")));

    expect(app.filter((file) => /(^|\/)route\.(ts|tsx|js)$/.test(file)).map(named)).toEqual([]);
    expect(files.filter((file) => /(^|\/)(middleware|proxy)\.(ts|js)$/.test(file)).map(named)).toEqual([]);
    expect(
      readdirSync(path.resolve(SRC, "..")).filter((name) => /^(middleware|proxy)\.(ts|js)$/.test(name)),
    ).toEqual([]);
    expect(source.filter((file) => /["']use server["']/.test(code(file))).map(named)).toEqual([]);
  });

  test("test_nothing_in_the_source_touches_storage_the_console_or_the_address", () => {
    const reaching = source
      .filter((file) =>
        /\b(localStorage|sessionStorage|indexedDB|document\.cookie|cookieStore|serviceWorker|sendBeacon|console\.\w+|history\.(push|replace)State|location\.(assign|replace|href\s*=|search|hash\s*=)|useRouter|useSearchParams|window\.open)\b/.test(
          code(file),
        ),
      )
      .map(named);

    expect(reaching).toEqual([]);
  });

  test("test_nothing_is_put_into_the_page_as_markup", () => {
    const risky = source
      .filter((file) => /dangerouslySetInnerHTML|\.innerHTML\s*=|\.outerHTML\s*=|insertAdjacentHTML|document\.write|\beval\(|new Function\(/.test(code(file)))
      .map(named);

    expect(risky).toEqual([]);
  });

  test("test_no_example_names_a_place", () => {
    const areas = (readRecorded("areas").body as { data: AreasData }).data.areas;
    const names = areas.flatMap((area) => [area.name, area.borough]);

    expect(EXAMPLES).toHaveLength(3);
    for (const example of EXAMPLES) {
      // A proper noun is a word with a capital that does not open the sentence.
      const capitals = example.split(/\s+/).slice(1).filter((word) => /^[A-Z]/.test(word));
      expect(capitals).toEqual([]);
      expect(names.filter((name) => example.toLowerCase().includes(name.toLowerCase()))).toEqual([]);
      expect(example.length).toBeLessThanOrEqual(600);
    }
  });
});
