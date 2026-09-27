import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";

import { RESULTS, SOURCE } from "@/content/search";
import { recordedAnswer } from "@/lib/api/recorded";

import { rulesOf } from "../../../test/support/css";
import { factsCited, Sentence } from "./Sentence";

const explained = recordedAnswer("explain_top", "explanations-first").body.data;

describe("a sentence", () => {
  const [explanation] = explained.explanations;
  const reason = explanation?.reasons[0];
  if (!reason) throw new Error("the recording gives no reason");

  test("test_a_sentence_is_shown_as_it_came_with_nothing_added", () => {
    const { container } = render(<Sentence sentence={reason} facts={explained.facts} />);

    expect(container.querySelector("p")?.textContent).toBe(reason.text);
  });

  test("test_the_source_of_a_sentence_is_the_fact_it_is_about", () => {
    const orientation = explanation?.orientation;
    if (!orientation) throw new Error("the recording gives no orientation");

    expect(factsCited(reason, explained.facts).map((fact) => fact.fact_id)).toEqual(reason.fact_ids);
    expect(factsCited(orientation, explained.facts)[0]?.kind).toBe("area");
    expect(factsCited({ fact_ids: ["not/a/fact"] }, explained.facts)).toEqual([]);
  });

  test("test_a_sentence_is_not_held_inside_a_paragraph_with_its_source", () => {
    // A button's panel inside a paragraph is markup a browser would rearrange.
    const { container } = render(<Sentence sentence={reason} facts={explained.facts} />);

    expect(container.querySelectorAll("p button, p div")).toHaveLength(0);
  });

  test("test_a_sentence_ends_in_the_key_of_its_source_unless_it_is_told_that_its_source_stands_elsewhere", () => {
    // On a result as it is first shown no key stands: a person who walked the website
    // asked for the key of a source to stand in the working alone. The sentence is as it
    // came either way, and its source is the same fact wherever its key stands.
    const { unmount } = render(<Sentence sentence={reason} facts={explained.facts} of="a reason" />);
    expect(screen.getByRole("button", { name: SOURCE.buttonFor("a reason") })).toBeInTheDocument();
    unmount();

    const { container } = render(<Sentence sentence={reason} facts={explained.facts} of="a reason" source={false} />);
    expect(container.querySelector("p")?.textContent).toBe(reason.text);
    expect(container.textContent).toBe(reason.text);
    expect(container.querySelectorAll("button, a")).toHaveLength(0);
  });

  test("test_a_sentence_a_model_wrote_says_so_whether_or_not_its_key_stands_beside_it", () => {
    const written = { ...reason, origin: "model" as const };
    const { container } = render(<Sentence sentence={written} facts={explained.facts} source={false} />);

    expect(container.textContent).toBe(`${reason.text}${RESULTS.byModel}`);
  });

  test("test_a_sentence_is_laid_out_by_the_width_of_what_it_stands_in_and_not_of_the_screen", () => {
    // In the middle column of a wide screen a result is as narrow as a phone is.
    const rules = rulesOf(readFileSync(path.join(__dirname, "Sentence.module.css"), "utf8"));
    const conditions = [...new Set(rules.map((rule) => rule.under).filter((under): under is string => under !== null))];

    expect(conditions).toEqual(["@container (max-width: 30rem)"]);
  });
});
