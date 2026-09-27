import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";

import { ABOUT } from "@/content/about";
import { KNOWN } from "@/content/kit";

import { faultsIn } from "../../../../test/support/axe";
import { rulesOf } from "../../../../test/support/css";
import { sizeOf } from "../drawings";
import { Approx, NoData } from "./Approx";

const SRC = path.resolve(__dirname, "..", "..", "..");
const CSS = readFileSync(path.join(__dirname, "Approx.module.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const STYLES = rulesOf(CSS).filter((rule) => !/forced-colors/.test(rule.under ?? ""));
const setsOf = (selector: string) =>
  new Map(
    STYLES.filter((rule) => rule.selector === selector).flatMap((rule) =>
      [...rule.sets].map(([property, value]): [string, string] => [property, value.replace(/\s+/g, " ")]),
    ),
  );

/** Every file of the website that is no test, by its path from `src`, with what is written in it. */
function theWebsite(folder = SRC): [file: string, written: string][] {
  return readdirSync(folder, { withFileTypes: true }).flatMap((entry): [string, string][] => {
    const file = path.join(folder, entry.name);
    if (entry.isDirectory()) return theWebsite(file);
    if (!/\.tsx?$/.test(entry.name) || /\.test\.tsx?$|\.d\.ts$/.test(entry.name)) return [];
    return [[path.relative(SRC, file), readFileSync(file, "utf8")]];
  });
}

describe("what is not whole, and what is not known", () => {
  test("test_what_is_not_whole_is_said_in_the_founders_two_words_after_its_mark_and_in_nothing_else", () => {
    const { container } = render(<Approx />);

    // The founder: "just show the incomplete data icon and simple text of 'approx data'".
    expect(KNOWN.some).toBe("approx data");
    expect(container.textContent).toBe("approx data");
    // The mark is dress, and is kept from whoever hears the page: the two words are heard.
    const mark = container.querySelector("[aria-hidden='true']") as HTMLElement;
    expect(mark.style.getPropertyValue("--art")).toBe('url("/art/ui-approx.png")');
    expect(mark.textContent).toBe("");
    expect(mark.nextElementSibling?.textContent).toBe(KNOWN.some);
    expect(screen.queryByRole("img")).toBeNull();
    // It opens nothing and takes no press.
    expect(container.querySelectorAll("button, a, summary")).toHaveLength(0);
  });

  test("test_the_mark_is_one_step_of_a_band_shown_at_its_own_size", () => {
    const { container } = render(<Approx />);
    const mark = container.querySelector("[aria-hidden='true']") as HTMLElement;
    const { width, height } = sizeOf("ui-approx");

    // A step of a band is nine art pixels by six, and so is its mark.
    expect([width, height]).toEqual([9, 6]);
    expect([mark.style.getPropertyValue("--w"), mark.style.getPropertyValue("--h")]).toEqual(["9", "6"]);
    // It is never stretched: its width and its height are its own, times the art pixel.
    expect([setsOf(".mark").get("width"), setsOf(".mark").get("height")]).toEqual([
      "calc(var(--px) * var(--w))",
      "calc(var(--px) * var(--h))",
    ]);
    expect(setsOf(".mark").get("image-rendering")).toBe("pixelated");
  });

  test("test_what_is_not_known_is_said_to_be_not_known_beside_a_step_that_holds_nothing", () => {
    const { container } = render(<NoData />);

    expect(KNOWN.none).toBe("no data");
    expect(container.textContent).toBe("no data");
    const step = container.querySelector(".blank") as HTMLElement;
    expect(step).toHaveAttribute("aria-hidden", "true");
    // It is as large as the mark of what is not whole, has the whole edge of a step and
    // holds nothing: it is neither nought nor the middle.
    expect(setsOf(".blank").get("width")).toBe("calc(var(--px) * 9)");
    expect(setsOf(".blank").get("height")).toBe("calc(var(--px) * 6)");
    expect(setsOf(".blank").get("border")).toBe("var(--px) solid var(--ink)");
    expect(setsOf(".blank").get("background")).toBe("var(--page)");
  });

  test("test_the_two_words_are_read_in_the_reading_face_in_ink_and_nothing_of_it_warns", () => {
    expect(setsOf(".said").get("font")).toBe("400 var(--size-small) / 1.3 var(--font-say)");
    expect(setsOf(".said").get("color")).toBe("var(--ink)");
    // Nothing of it is red, nothing is dimmed, and no rule of it is in pieces.
    expect(/poppy|tradeoff|error|opacity|dashed|dotted/.test(CSS)).toBe(false);
  });

  test("test_it_may_say_other_words_where_it_is_handed_them", () => {
    const { container } = render(<Approx says="estimated" />);

    expect(container.textContent).toBe("estimated");
  });

  test("test_each_stands_where_it_is_told_to_and_is_drawn_the_same_wherever_it_stands", () => {
    const { container } = render(
      <p>
        <Approx className="beside-a-band" />
        <NoData className="under-a-name" />
      </p>,
    );
    const [some, none] = [...(container.firstElementChild as HTMLElement).children];

    expect([...(some as HTMLElement).classList]).toEqual(["approx", "beside-a-band"]);
    expect([...(none as HTMLElement).classList]).toEqual(["approx", "under-a-name"]);
    // Each says how much of its figure is known, to whatever lays it out.
    expect([some?.getAttribute("data-known"), none?.getAttribute("data-known")]).toEqual(["some", "none"]);
  });

  test("test_neither_has_an_accessibility_fault", async () => {
    const { container } = render(
      <p>
        <Approx /> <NoData />
      </p>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});

describe("the mark and its two words are one part, and its words are written once", () => {
  const files = theWebsite();
  /** What is written in a file, with what is said of the code, and not by it, left out. */
  const code = (written: string) => written.replace(/\/\*[\s\S]*?\*\/|(?<![:"'`])\/\/.*$/gm, "");

  test("test_the_two_words_of_each_are_written_in_one_file_of_site_copy_and_in_no_other_file_of_the_website", () => {
    // The two words were written in two files, and drawn by two parts of one name: a change
    // to the label was two changes, and one page could say it otherwise than the next.
    const writes = (words: string) => files.filter(([, written]) => code(written).includes(`"${words}"`)).map(([file]) => file);

    expect(files.length).toBeGreaterThan(200);
    expect(writes(KNOWN.some)).toEqual(["content/kit.ts"]);
    expect(writes(KNOWN.none)).toEqual(["content/kit.ts"]);
    // The key to the drawings quotes the two words, and takes them from there.
    expect(ABOUT.band.states.part).toContain(`"${KNOWN.some}"`);
    expect(files.filter(([, written]) => code(written).includes("approx data")).map(([file]) => file)).toEqual(["content/kit.ts"]);
  });

  test("test_the_mark_is_named_by_one_part_which_is_the_kits_and_every_page_draws_it_by_that_part", () => {
    // The list of the drawings names every drawing, and draws none.
    const names = files
      .filter(([file, written]) => file !== "lib/art/names.ts" && code(written).includes('"ui-approx"'))
      .map(([file]) => file);
    const draws = files.filter(([, written]) => /<Approx\b/.test(code(written))).map(([file]) => file);
    const takes = (written: string) =>
      [...written.matchAll(/import \{[^}]*\bApprox\b[^}]*\} from "([^"]+)";/g)].map(([, from]) => from ?? "");

    expect(names).toEqual(["components/kit/Approx/Approx.tsx"]);
    // A result and its lines, its working, the page of an area, a comparison and its cells,
    // and the key to the drawings.
    expect(draws.filter((file) => !file.startsWith("components/kit/")).sort()).toEqual([
      "components/CompareTable/CompareTable.tsx",
      "components/CompareTable/VibeMark.tsx",
      "components/Portrait/Portrait.tsx",
      "components/ResultList/ResultCard.tsx",
      "components/ResultList/parts.tsx",
      "components/Strip/Strip.tsx",
      "components/VibesList/BandKey.tsx",
    ]);
    for (const [file, written] of files.filter(([file]) => draws.includes(file) && !file.startsWith("components/kit/"))) {
      expect([file, takes(written).map((from) => from.replace(/^@\/components\/|^(\.\.\/)+/, ""))]).toEqual([file, ["kit/Approx/Approx"]]);
    }
    // No other file of the website is a part of that name.
    expect(files.map(([file]) => file).filter((file) => /(^|\/)Approx\.tsx$/.test(file))).toEqual(["components/kit/Approx/Approx.tsx"]);
  });
});
