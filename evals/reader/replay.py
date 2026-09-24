"""A model's answers on disk, read again through the reader the service uses.

    uv run python evals/reader/replay.py
    uv run python evals/reader/replay.py --show
    uv run python evals/reader/replay.py --look 1

No provider is called and nothing is paid for. `answers/` holds what one
model answered to each of a set of made-up sentences, word for word, and
whether a call was refused or failed. A stand-in hands each answer back to
the reader, which checks it as it would check a fresh one. So a change to the
guard is measured on the same answers, as often as it is wanted.

It says what the guard does with these answers. It cannot say what the model
would answer to another sentence, or to the same one on another day: some
sentences were asked more than once, and each asking is a look of its own.

A sentence that is in the evaluation set is judged by its case there. The
others are judged by the cases in `answers/cases/`, which are no part of the
evaluation set and move no floor.

This file and `stand_in.py` are the two here that import the API.
"""

import argparse
import importlib.util
import json
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from burro_api.providers.interface import ModelError, ModelReply
from burro_api.reader import ModelInterpreter

_SPEC = importlib.util.spec_from_file_location("reader_score", Path(__file__).with_name("score.py"))
assert _SPEC is not None and _SPEC.loader is not None
score = importlib.util.module_from_spec(_SPEC)
sys.modules.setdefault("reader_score", score)
_SPEC.loader.exec_module(score)

HERE = Path(__file__).resolve().parent
ANSWERS = HERE / "answers"
MODEL = "gemini-3.5-flash-lite"


class Answered:
    """Stands in for a provider. It hands back the answer on disk, or fails as the call did."""

    def __init__(self) -> None:
        self.row: dict[str, Any] = {}
        self.calls = 0

    def complete(self, **sent: Any) -> ModelReply:
        self.calls += 1
        if "output" not in self.row:
            raise ModelError
        return ModelReply(
            str(self.row["output"]),
            input_tokens=int(self.row.get("input_tokens", 0)),
            output_tokens=int(self.row.get("output_tokens", 0)),
            cache_read_tokens=0,
        )


def answers_of(folder: Path, model: str) -> list[dict[str, Any]]:
    """Every answer on disk for one model, in the order of its sentences and its looks."""
    lines = (folder / f"{model}.jsonl").read_text(encoding="utf-8").splitlines()
    return [cast(dict[str, Any], json.loads(line)) for line in lines if line.strip()]


def cases_for(folder: Path, release: Any) -> dict[str, Any]:
    """The case each sentence is judged by: the evaluation set's, and those beside the answers."""
    found: dict[str, Any] = {}
    for where in (score.CASES, folder / "cases"):
        cases, problems = score.load_cases(where, release)
        if problems:
            raise SystemExit("\n".join(f"bad case: {problem}" for problem in problems))
        found |= {case.id: case for case in cases}
    return found


def replayed(
    rows: Sequence[dict[str, Any]], cases: dict[str, Any], release: Any
) -> list[tuple[dict[str, Any], Any, int]]:
    """Each answer, scored as the scorer scores it, and how many calls the reader made for it."""
    names = score.Names(release)
    answered = Answered()
    reader = ModelInterpreter(answered, MODEL, 2048, 6.0)
    found: list[tuple[dict[str, Any], Any, int]] = []
    for row in rows:
        case = cases.get(str(row["id"]))
        if case is None or case.text != row["text"]:
            raise SystemExit(f"{row['id']}: no case holds these words")
        answered.row, before = row, answered.calls
        found.append((row, score.score(case, reader, release, names), answered.calls - before))
    return found


def counted(found: Sequence[tuple[dict[str, Any], Any, int]]) -> dict[str, int]:
    """The counts a floor is held to, over every answer that was read again."""
    scored = [one for _, one, _ in found]
    offers = Counter(one.offer for one in scored)
    outcomes = Counter(one.outcome for one in scored)
    rules = [one for one in scored if one.offer is None and one.outcome is not score.Outcome.FAILED]
    return {
        "answers": len(found),
        "calls the reader made": sum(calls for _, _, calls in found),
        "answered by the rules, with no call or in a model's place": len(rules),
        "right": offers[score.Offered.RIGHT]
        + sum(one.outcome is score.Outcome.CORRECT for one in rules),
        "in part": offers[score.Offered.PARTIAL]
        + sum(one.outcome is score.Outcome.PARTIAL for one in rules),
        "not read": offers[score.Offered.NOT_READ]
        + sum(one.outcome in (score.Outcome.DECLINED, score.Outcome.SUGGESTED) for one in rules),
        "a guess nobody asked for": offers[score.Offered.UNASKED],
        "backwards, offered with no guess marked": offers[score.Offered.BACKWARDS],
        "backwards, marked as the guess": offers[score.Offered.BACKWARDS_GUESS],
        "backwards, applied": outcomes[score.Outcome.REVERSED],
        "never to be offered, and offered": offers[score.Offered.NEVER],
        "applied with no press": offers[score.Offered.APPLIED],
        "right readings of the rules lost": sum(one.lost for one in scored),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read a model's answers on disk again.")
    parser.add_argument("--answers", type=Path, default=ANSWERS, help="the folder of answers")
    parser.add_argument("--model", default=MODEL, help="the model whose answers to read")
    parser.add_argument("--look", type=int, help="read only this look of each sentence")
    parser.add_argument("--show", action="store_true", help="list each sentence that went wrong")
    args = parser.parse_args(argv)
    out = sys.stdout.write
    release = score.load_release(None)
    rows = answers_of(args.answers, args.model)
    if args.look is not None:
        rows = [row for row in rows if row["look"] == args.look]
    found = replayed(rows, cases_for(args.answers, release), release)
    for name, count in counted(found).items():
        out(f"{name:<60}{count:>5}\n")
    wrong = (
        score.Offered.APPLIED,
        score.Offered.NEVER,
        score.Offered.BACKWARDS_GUESS,
        score.Offered.BACKWARDS,
        score.Offered.UNASKED,
    )
    for row, one, _ in found if args.show else ():
        if one.offer in wrong or one.lost or one.outcome is score.Outcome.REVERSED:
            told = "; ".join(
                finding.what
                for finding in one.findings
                if finding.verdict in (score.Verdict.REVERSED, score.Verdict.UNASKED)
            )
            what = "lost" if one.lost else (one.offer or one.outcome).value
            out(f"  [{row['id']} look {row['look']}] {what}: {one.case.text[:70]}: {told}\n")
    # The floor is held to the first look, which is one asking of every sentence.
    # The later looks are of the few sentences that went wrong, asked again.
    failed = score.offers_gate([one for row, one, _ in found if row["look"] <= 1])
    out("\n" + ("\n".join(f"FAIL: {reason}" for reason in failed) if failed else "PASS") + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
