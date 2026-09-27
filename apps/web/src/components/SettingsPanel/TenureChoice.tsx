"use client";

import { TENURE_CHOICE } from "@/content/search";
import { KIND_OF_SEARCH } from "@/content/settings";
import type { Tenure } from "@/lib/api/schema";
import { useDraft } from "@/lib/search/draft";

import { Radios } from "./fields";

/** The kinds of search, in the order they are asked in. The service calls the third a visit. */
const KINDS: readonly Tenure[] = ["rent", "buy", "visit"];

/** What each is called. The words for renting and buying are older, and are read from where they stand. */
const called = (kind: Tenure) => (kind === "visit" ? KIND_OF_SEARCH.visit : TENURE_CHOICE[kind]);

interface Props {
  readonly tenure: Tenure;
  /**
   * Told of the choice. Before anything is asked for, the page swaps in what a search of
   * that kind starts from and sends nothing. After, it is an edit like any other.
   */
  readonly onChoose: (tenure: Tenure) => void;
  readonly version: number;
  readonly problem?: string | null;
}

/**
 * Renting, buying or visiting: three radio buttons, drawn as Town Map's buttons, of which
 * the one that is chosen is amber. They stand side by side and each is as wide as the next.
 *
 * Visiting is a kind of search of its own, for whoever is looking for where to stay. It
 * holds no budget, no number of bedrooms and no kind of home: what holds the choice draws
 * none of them while it is chosen.
 */
export function TenureChoice({ tenure, onChoose, version, problem = null }: Props) {
  const [shown, show] = useDraft(tenure, version);
  return (
    <Radios
      legend={KIND_OF_SEARCH.legend}
      options={KINDS.map((value) => ({ value, label: called(value) }))}
      value={shown}
      problem={problem}
      thing={{ kind: "tenure" }}
      even
      onChange={(chosen) => {
        show(chosen);
        onChoose(chosen);
      }}
    />
  );
}
