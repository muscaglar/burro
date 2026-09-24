import { render } from "@testing-library/react";

import { recordedAnswer } from "@/lib/api/recorded";

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
});
