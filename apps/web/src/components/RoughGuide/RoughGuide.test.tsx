import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";

import { recordedAnswer } from "@/lib/api/recorded";

import { faultsIn } from "../../../test/support/axe";
import { rulesOf } from "../../../test/support/css";
import { RoughLabel, RoughNote } from "./RoughGuide";

const [told] = recordedAnswer("get_meta", "meta").body.data.rough_guides;
if (told === undefined) throw new Error("The recording holds no rough guide.");
const STYLES = rulesOf(readFileSync(path.join(__dirname, "RoughGuide.module.css"), "utf8"));

describe("what a vibe that is a rough guide says of itself", () => {
  test("test_the_label_is_the_apis_word_and_is_read_out_after_the_name_it_stands_beside", () => {
    const { container } = render(
      <p>
        Village feel
        <RoughLabel told={told} />
      </p>,
    );

    expect(container.textContent).toBe(`Village feel, ${told.label}`);
    // The comma is for whoever hears the page. What is drawn is the label alone.
    expect(container.querySelector(".visually-hidden")?.textContent).toBe(", ");
    expect(container.querySelector("[data-rough-guide='label']")?.lastChild?.textContent).toBe(told.label);
  });

  test("test_the_note_says_the_label_and_the_sentence_word_for_word", () => {
    render(<RoughNote told={told} />);

    expect(screen.getByRole("note")).toHaveTextContent(`${told.label}. ${told.why}`);
    expect(screen.getByRole("note").textContent).toBe(`${told.label}. ${told.why}`);
  });

  test("test_the_note_names_its_vibe_where_it_stands_apart_from_it", () => {
    render(<RoughNote told={told} of="Village feel" />);

    expect(screen.getByRole("note").textContent).toBe(`Village feel: ${told.label}. ${told.why}`);
  });

  test("test_beside_a_label_that_is_already_drawn_the_note_says_the_sentence_alone", () => {
    render(<RoughNote told={told} labelled />);

    expect(screen.getByRole("note").textContent).toBe(told.why);
  });

  test("test_of_a_vibe_that_is_as_sure_as_the_rest_nothing_is_drawn", () => {
    const { container } = render(
      <>
        <RoughLabel told={null} />
        <RoughNote told={null} />
        <RoughNote told={null} of="Leafy" />
      </>,
    );

    expect(container.innerHTML).toBe("");
  });

  test("test_the_label_is_told_from_the_name_by_more_than_colour", () => {
    const label = STYLES.filter((rule) => rule.selector === ".label").flatMap((rule) => [...rule.sets.keys()]);

    expect(label).toEqual(expect.arrayContaining(["border", "font-weight"]));
  });

  test("test_neither_has_an_accessibility_fault", async () => {
    const { container } = render(
      <main>
        <h1>
          Village feel
          <RoughLabel told={told} />
        </h1>
        <RoughNote told={told} of="Village feel" />
      </main>,
    );

    expect(await faultsIn(container)).toEqual([]);
  });
});
