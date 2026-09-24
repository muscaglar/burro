"""The guard on a model, measured on the cases with a model that is a stand-in.

    uv run python evals/reader/stand_in.py
    uv run python evals/reader/stand_in.py --show

No provider is called and nothing is paid for. Two stand-ins answer in a
model's place, through the reader the service uses and the guard it keeps:

`right` reads each case as the case says a careful person would. What comes
through is the most a model could add that reads every sentence well.

`backwards` raises every thing a sentence names, whatever is said of it. What
comes through is what the guard lets a careless model do.

Nothing a model reads is applied, so what comes through is what is offered
with a guess marked. Each stand-in is counted twice over: by what became of
the search, which is what the rules made of it, and by what a person would
get who pressed every guess.

Each is run twice: sent the words alone, and sent the search settings with
them, as `BURRO_MODEL_SENDS_SETTINGS` decides in the service. A stand-in uses
only what it is sent. Sent the words alone, it cannot know what the search
holds, so it names a journey only by a name that is in the words.

A stand-in cannot say how well a real model reads. It says what the guard
lets through of an answer, and whether that depends on what was sent.

This is the one file here that imports the API.
"""

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter
from collections.abc import Callable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any, cast

from burro_api.providers.interface import ModelReply
from burro_api.reader import MAX_EDITS, ModelInterpreter
from burro_core.catalogue import FEATURES, TAGS
from burro_core.ids import FeatureId, Notice, Polarity, TagId
from burro_core.lexicon import lexicon_of
from burro_core.release import InMemoryRelease

_SPEC = importlib.util.spec_from_file_location("reader_score", Path(__file__).with_name("score.py"))
assert _SPEC is not None and _SPEC.loader is not None
score = importlib.util.module_from_spec(_SPEC)
sys.modules.setdefault("reader_score", score)
_SPEC.loader.exec_module(score)

Edit = dict[str, Any]
Answer = dict[str, Any]
GROUPS = ("budget_ops", "commute_ops", "weight_ops", "tag_ops", "area_ops", "setting_ops")
# From best to worst, to choose what a model that picked its words well would leave.
BEST_FIRST = tuple(reversed(tuple(score.Outcome)))
A_FIGURE = re.compile(r"[0-9][0-9,]*")


def nothing() -> Answer:
    """An answer that fits the schema and asks for nothing."""
    empty: Answer = {group: [] for group in GROUPS}
    return {"status": "ok", **empty, "policy_flags": [], "unmet": []}


def weight(feature_id: str, **changes: Any) -> Edit:
    edit: Edit = {
        "action": "nudge",
        "feature_id": feature_id,
        "value": 0.0,
        "step": "up_large",
        "direction": "default",
        "provenance": "stated",
    }
    return edit | changes


def tag(tag_id: str, **changes: Any) -> Edit:
    edit: Edit = {
        "action": "nudge",
        "tag_id": tag_id,
        "value": 0.0,
        "step": "up_large",
        "toward": "default",
        "provenance": "stated",
    }
    return edit | changes


def journey(**changes: Any) -> Edit:
    edit: Edit = {
        "action": "add",
        "destination_text": "",
        "position": 0,
        "mode": "unchanged",
        "max_minutes": 0,
        "strictness": "unchanged",
        "step": "none",
        "provenance": "stated",
    }
    return edit | changes


def budget(**changes: Any) -> Edit:
    edit: Edit = {
        "action": "set",
        "tenure": "unchanged",
        "amount": 0,
        "segment": "unchanged",
        "strictness": "unchanged",
        "step": "none",
        "provenance": "stated",
    }
    return edit | changes


def parts_of(text: str) -> list[str]:
    """The whole of a text, and each sentence of it, for a model to rest its edits on."""
    found = [part.strip(" .!?") for part in re.split(r"(?<=[.!?])\s+|\n", text)]
    # A text that is marks alone has no part to rest on but itself.
    return list(dict.fromkeys(part for part in (text.strip(" .!?"), *found) if part)) or [text]


class Known:
    """What a stand-in knows of the release: every name a place or an area goes by."""

    def __init__(self, release: InMemoryRelease) -> None:
        self.places = {p.place_id: (p.name, *p.aliases) for p in release.places}
        self.areas = {a.area_id: (a.name, *a.aliases) for a in release.neighbourhoods}
        self.lexicon = lexicon_of(release.manifest.gritty_variant)

    @staticmethod
    def typed(text: str, names: Sequence[str]) -> str:
        """The name as it stands in the text, or nothing where none of them does."""
        for name in sorted(names, key=len, reverse=True):
            at = text.casefold().find(name.casefold())
            if at >= 0:
                return text[at : at + len(name)]
        return ""


def _risen(thing: str) -> tuple[str, Edit]:
    kind, _, named = thing.partition(":")
    if kind == "feature":
        return "weight_ops", weight(named)
    scale = TAGS[TagId(named)].low_end is not None
    return "tag_ops", tag(named, toward="high" if scale else "default")


def _fallen(thing: str) -> tuple[str, Edit]:
    kind, _, named = thing.partition(":")
    if kind == "feature":
        if FEATURES[FeatureId(named)].polarity is Polarity.EITHER:
            return "weight_ops", weight(named, direction="less")
        return "weight_ops", weight(named, action="remove", step="none")
    if TAGS[TagId(named)].low_end is not None:
        return "tag_ops", tag(named, toward="low")
    return "tag_ops", tag(named, action="remove", step="none")


def _by_position(case: Any, place_id: str, sent: Mapping[str, Any] | None) -> int:
    """Where a journey stands in the search, if the stand-in was sent the search."""
    if sent is None:
        return 0
    held = [commute.place_id for commute in case.start.commutes]
    return held.index(place_id) + 1 if place_id in held else 0


def _journeys(case: Any, known: Known, sent: Mapping[str, Any] | None) -> Iterator[Edit]:
    expect = case.expect
    for wanted, action in (
        *((j, "add") for j in expect.add),
        *((j, "remove") for j in expect.remove),
    ):
        named = known.typed(case.text, known.places[wanted.place_id])
        position = 0 if named else _by_position(case, wanted.place_id, sent)
        if not named and not position:
            # Nothing in the words says which journey, and the search was not sent.
            continue
        yield journey(
            action=("update" if position else "add") if action == "add" else "remove",
            destination_text=named,
            position=position,
            mode=wanted.mode.value if wanted.mode else "unchanged",
            max_minutes=wanted.max_minutes or 0,
            strictness=wanted.strictness.value if wanted.strictness else "unchanged",
        )


def _money(case: Any) -> Iterator[Edit]:
    expect = case.expect
    if expect.no_amount:
        yield budget(action="clear")
        return
    said = expect.amount or expect.segment or expect.strictness or expect.tenure
    if not said:
        return
    least, most = expect.amount or (0, 0)
    figures = [int(found.replace(",", "")) for found in A_FIGURE.findall(case.text)]
    within = [figure for figure in figures if least <= figure <= most]
    stepped = expect.amount is not None and not within
    yield budget(
        action="nudge" if stepped else "set",
        # A figure that is in the words, or a step towards what is asked for.
        amount=within[0] if within else 0,
        step=("none" if not stepped else "down_small" if most < _held(case) else "up_small"),
        tenure=expect.tenure.value if expect.tenure else "unchanged",
        segment=expect.segment or "unchanged",
        strictness=expect.strictness.value if expect.strictness else "unchanged",
    )


def _held(case: Any) -> int:
    return case.start.budget.amount or 0


def right(case: Any, known: Known, sent: Mapping[str, Any] | None) -> Answer:
    """The answer of a model that reads a case as the case says it is meant."""
    expect = case.expect
    answer = nothing()
    if expect.notice == Notice.OFF_TOPIC.value:
        return answer | {"status": "off_topic"}
    if expect.notice == Notice.NEUTRAL_PLACES.value:
        answer["policy_flags"] = ["avoid_group"]
    answer["unmet"] = [category.value for category in expect.unmet]
    for thing in (*expect.rise, *(any_of[0] for any_of in expect.rise_any)):
        group, edit = _risen(thing)
        answer[group].append(edit)
    for thing in (*expect.fall, *(any_of[0] for any_of in expect.fall_any)):
        group, edit = _fallen(thing)
        answer[group].append(edit)
    answer["commute_ops"] += _journeys(case, known, sent)
    for action, areas in (
        ("exclude", expect.exclude),
        ("only", expect.only),
        ("clear", expect.clear),
    ):
        for area_id, _ in areas:
            named = known.typed(case.text, known.areas[area_id])
            if named:
                answer["area_ops"].append(
                    {"action": action, "area_text": named, "provenance": "stated"}
                )
    answer["budget_ops"] += _money(case)
    return answer


def backwards(case: Any, known: Known, sent: Mapping[str, Any] | None) -> Answer:
    """The answer of a model that raises every thing a sentence names, whatever is said of it."""
    text = case.text
    answer = nothing()
    seen: set[str] = set()
    for phrase, target in known.lexicon.items():
        found = re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", text.casefold())
        if found is None:
            continue
        words = text[found.start() : found.end()]
        for thing in (*target.features, *target.tags):
            if thing.value not in seen and len(seen) < 12:
                seen.add(thing.value)
                if thing in target.features:
                    answer["weight_ops"].append(weight(thing.value, words=words))
                else:
                    answer["tag_ops"].append(tag(thing.value, action="set", value=1.0, words=words))
    for names in known.places.values():
        named = known.typed(text, names)
        if named:
            answer["commute_ops"].append(journey(destination_text=named, words=named))
    for names in known.areas.values():
        named = known.typed(text, names)
        if named:
            answer["area_ops"] += [
                {"action": action, "area_text": named, "provenance": "stated", "words": named}
                for action in ("exclude", "only")
            ]
    answer["commute_ops"], answer["area_ops"] = answer["commute_ops"][:3], answer["area_ops"][:4]
    return answer


def resting_on(answer: Answer, words: str) -> Answer:
    """`answer`, with every edit that names no words resting on `words`."""
    rested = dict(answer)
    for group in GROUPS:
        rested[group] = [{"words": words} | edit for edit in answer[group]][:MAX_EDITS]
    return rested


Reads = Callable[[Any, Known, Mapping[str, Any] | None], Answer]


class StandIn:
    """Stands in for a provider. It answers from what it was sent, and keeps none of it."""

    def __init__(self, reads: Reads, cases: Mapping[str, Any], known: Known) -> None:
        self._reads = reads
        self._cases = cases
        self._known = known
        # The words every edit rests on that names none of its own.
        self.words = ""

    def complete(self, **sent: Any) -> ModelReply:
        turn = cast(dict[str, Any], json.loads(sent["user"]))
        case = self._cases[turn["request"]]
        answer = resting_on(self._reads(case, self._known, turn.get("spec")), self.words)
        return ModelReply(json.dumps(answer), input_tokens=0, output_tokens=0, cache_read_tokens=0)


def measured(reads: Reads, with_settings: bool, cases: Sequence[Any], release: Any) -> list[Any]:
    """Every case, scored as the scorer scores it, with the best words a model could rest on."""
    known, names = Known(release), score.Names(release)
    model = StandIn(reads, {case.text: case for case in cases}, known)
    reader = ModelInterpreter(model, "stand-in", 2048, 6.0, with_settings=with_settings)
    found: list[Any] = []
    for case in cases:
        tried: list[Any] = []
        for words in parts_of(case.text):
            model.words = words
            tried.append(score.score(case, reader, release, names))
        found.append(min(tried, key=lambda scored: BEST_FIRST.index(scored.outcome)))
    return found


def counted(scored: Sequence[Any]) -> dict[str, int]:
    counts = Counter(one.outcome for one in scored)
    return {score.HEADINGS[outcome]: counts[outcome] for outcome in (*score.COLUMNS, "failed")}


def offered(scored: Sequence[Any]) -> dict[str, int]:
    """What became of what was offered with a guess, and what of the rules' was lost."""
    counts = Counter(one.offer for one in scored if one.offer is not None)
    found = {score.OFFER_HEADINGS[offer]: counts[offer] for offer in score.OFFER_COLUMNS}
    return found | {"rules' readings lost": sum(one.lost for one in scored)}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Measure the guard with a stand-in for a model.")
    parser.add_argument("--show", action="store_true", help="list each case the settings move")
    args = parser.parse_args(argv)
    out = sys.stdout.write
    release = score.load_release(None)
    cases, problems = score.load_cases(score.CASES, release)
    if problems:
        out(f"{len(problems)} cases cannot be scored as they are written\n")
        return 2
    holding = [case for case in cases if case.start != score.default_spec(case.tenure)]
    out(f"cases {len(cases)}, of which {len(holding)} start from a search that holds something\n")
    moved = 0
    for name, reads in (("right", right), ("backwards", backwards)):
        alone = measured(reads, False, cases, release)
        with_them = measured(reads, True, cases, release)
        out(f"\n{name}, sent the words alone:      {counted(alone)}\n")
        out(f"{name}, sent the settings as well: {counted(with_them)}\n")
        out(f"{name}, what was offered:           {offered(alone)}\n")
        differ = [
            (one, other)
            for one, other in zip(alone, with_them, strict=True)
            if one.outcome is not other.outcome
        ]
        moved += len(differ)
        out(f"{name}: {len(differ)} cases end otherwise when the settings are sent\n")
        for one, other in differ if args.show else ():
            out(f"  {one.case.id}: {one.outcome.value} alone, {other.outcome.value} with them\n")
    return 1 if moved else 0


if __name__ == "__main__":
    sys.exit(main())
