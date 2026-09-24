# Research behind the plan

Gathered on 2026-09-23, in two passes. Everything here supports [`../PLAN.md`](../PLAN.md). Treat it as a dated snapshot: licences, prices and model line-ups change, so re-check before relying on a specific figure.

## How to read this

| Folder | What is in it |
|---|---|
| `reports/` | One report per domain: recommendations, risks, open questions, claims that were not verified, and a compact list of every source checked |
| `verification/` | Four skeptics tried to refute the claims the plan depends on. Each file lists what was confirmed, what was wrong, and what to check in week one |
| `design/` | Three competing plans (lean, trust, experience), the merged plan, and the critique of it |

## Verification totals

| Area | Confirmed | Partly wrong | Refuted | Not verified |
|---|---|---|---|---|
| Data licences | 9 | 6 | 0 | 3 |
| Claude API | 14 | 2 | 1 | 0 |
| Platform and rules | 13 | 3 | 0 | 1 |
| Routing feasibility | 11 | 6 | 0 | 1 |
| **Total** | **47** | **17** | **1** | **5** |

## Limits of this research

- Web searches were made in part of the first pass. Later checks opened known addresses only.
- Few files were opened, and none is in the repository. Each report says which. The contents of the London bus timetable feed are unmeasured.
- Reddit, the EHRC site and parliament.uk were not read.
- Most pages were read through a reader that summarises. Re-check any quoted wording against the source before it goes into a legal document.
- Of a site whose terms forbid reading by a program, a report says only that a page was read, and on what day. A person opens each such page in a browser before anything rests on it.
- Nothing here is legal advice.

Throughout this folder, "not read" means that a page was not read, for whatever reason. It says nothing about the page, and nothing is implied about its publisher. A report makes no claim about what such a page holds, and a person opens the page before anything rests on it.

## Where the merged plan and the final plan differ

`design/unified.md` is the merged plan as the synthesis agent wrote it. `design/critique.md` found one blocker and fifteen major issues in it. `../PLAN.md` is the final version with those fixes applied, chiefly:

- Legal review was dropped on cost. Open questions are closed by design instead, and no professional has reviewed the result. See ADR 0007.
- Timeline moved from 13 weeks to 18, with founder hours budgeted per phase.
- Costs and quotas planned on the mid-tier model, since the smallest may retire during the build.
- Budget became a soft constraint, because official rent data understates new lets.
- Commute results gained nearest station, lines and on-demand route detail.
- Destination search extended to universities, hospitals and landmarks.
- The attributed Wikipedia excerpt was restored to profiles.
- Two tags renamed for places instead of residents.
- The rule that raw prompts are never logged was made explicit and testable.
