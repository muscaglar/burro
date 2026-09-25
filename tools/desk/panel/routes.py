"""What the panel answers: each route of it, as a function of the desk and what was sent.

The server hands a request here once it has held it to its own rules: the host, the
origin, the token. A word of a request is a key of a table the release gives, and a word
that is no key finds nothing. No route takes a figure: a figure is a publisher's.

A refusal is fixed text, and never repeats what was sent.

See docs/design/panel.md, and docs/design/desk.md, section 4.
"""

import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, cast

from burro_core.catalogue import (
    COUNTS_RESIDENTS,
    FEATURES,
    PART_MAX_HUNDREDTHS,
    of_a_tier,
    tags_of,
)
from burro_core.catalogue import PART_MAX_WHERE_RESIDENTS_COUNT as PART_MAX_BESIDE_RESIDENTS
from burro_core.ids import FeatureId, TagId
from burro_core.release import holds_the_name_of_a_place
from burro_pipeline import changes
from burro_pipeline.changes import Change, ChangesError, What
from burro_pipeline.derive import brand_table
from burro_pipeline.derive.brand_table import Table
from burro_pipeline.evidence import LockError, read_receipts
from burro_pipeline.evidence.receipt import RECEIPTS_FOLDER
from burro_pipeline.fetch.sources import LISTS, ListError, load_list
from burro_pipeline.upkeep import moved as between

from desk import records, server
from desk.panel import kept, look, numbers, preview
from desk.panel.look import Held
from desk.panel.preview import Search
from desk.server import Desk, Refused, bad, missing

NO_REASON: Final = "Say why, in a line of plain words of 500 characters at most."
NOT_HELD: Final = "The release holds no such figure, band, name or border to flag."
NOT_YOURS: Final = "There is no such line of yours to take back."
TAKEN_BACK: Final = "That line was taken back already."
UNREADABLE: Final = (
    "Not saved. The file of changes cannot be read as it stands. The desk printed which line."
)
NOT_YET_LEFT_OUT: Final = (
    "No build leaves a figure out yet. Flag it, and say why: a flag is listed for the person "
    "who builds."
)
NUMBERS_ARE_CORES: Final = numbers.SAYS
NOT_LOOKED_AT: Final = (
    "See what would move first. Nothing is kept that was not looked at as it stands now."
)
NOTHING_CHANGED: Final = "That is what stands already. Nothing was changed."
NO_OTHER: Final = (
    "No other release was named, so there is nothing to hold this one against. Start the "
    "desk with the release that is served today as well: make desk RELEASE=FOLDER BEFORE=FOLDER"
)
OTHER_CITY: Final = (
    "The release that is shown and the release it is held against are not of one city. Two "
    "cities are never held against each other"
)
FLAG: Final = frozenset({"of", "why", "leave_out"})
TAKE_BACK: Final = frozenset({"n", "why"})
PREVIEW: Final = frozenset({"what", "of", "now"})
KEEP: Final = frozenset({"what", "of", "now", "why", "seen"})
# What a person is told of a change that breaks a rule, by the rule. Fixed words: a
# refusal never repeats what was sent.
BREAKS: Final[Mapping[str, str]] = {
    "recipe_keeps_its_rules": (
        "A recipe comes to 100. No part is 60 or more, and beside a part that counts who "
        "lived there no part is over 40. Each part holds 1 at the least."
    ),
    "recipe_holds_cores_parts": (
        "A recipe holds the parts it has, each once. No part is added or taken out here."
    ),
    "change_is_of_its_kind": "The desk could not read what was sent.",
    "name_is_plain": (
        "A name is one line of plain words, of 40 characters at most, with no figure. A "
        "label may be longer, and may say again a figure the label it takes the place of "
        "says, and no other. Neither holds a word that calls a place safe or unsafe, praise "
        "or blame, or a word for a group of people."
    ),
    "says_what_it_cannot_see": (
        "What a vibe cannot see is said in lines of plain words, of 200 characters at most. "
        "A line that names the census or recorded crime is kept."
    ),
    "vibe_is_cores": (
        "A vibe of one way has no ends to name, and a scale has two. Nothing else of a vibe "
        "is changed here."
    ),
    "measure_is_cores": "Of a measure, its two labels are changed here, and nothing else.",
    "who_is_counted_is_named_by_core": (
        "A measure that counts who lived somewhere keeps its name: it says who was counted, "
        "and ends with the census they were counted at."
    ),
    "names_name_no_place": (
        "A name holds no name of an area, of a borough or of a place. A vibe and a measure "
        "are of every area alike."
    ),
    "held_off_stays_held_off": (
        "With the shares as they are, this vibe places no area: too little of its recipe "
        "has a figure. To move its shares to the parts that have one would place it on what "
        "is left of it. It waits for the figures, or for a change to the catalogue."
    ),
    "chain_moves_by_its_tier_alone": (
        "A chain of the table is moved by its tier alone. Its name, its kind and how the "
        "file of places writes it are changed in the table itself."
    ),
    "chain_is_named_as_it_is_written": (
        "A chain that is added is named as the file of places writes it: its name is one "
        "of the ways it is written."
    ),
    "row_is_a_row_of_the_table": (
        "A row of the table holds a name, a kind, a tier, and each way the file of places "
        "writes the chain. A kind is a grocer, a gym or coffee, a tier is premium, mid or "
        "value, and no two rows hold one spelling."
    ),
    changes.STALE: "What stood before has changed since this was shown. It is shown again.",
    changes.NOT_CARRIED: "The release does not carry that, so there is nothing to change.",
}


@dataclass(frozen=True)
class Panel:
    """What the panel holds: the release as it is served. It is made once, at the start."""

    held: Held
    # The searches that are ranked before and after a change.
    searches: tuple[Search, ...] = ()
    # What moved between another release and the one that is shown, where another was
    # named as the desk started. It is worked out once, as the step `moved` works it out.
    moved: Mapping[str, Any] | None = None

    @property
    def synthetic(self) -> bool:
        return self.held.synthetic

    def answer(self, desk: Desk, what: str, of: str | None, sent: object) -> dict[str, Any]:
        """What one route answers. Raises `Refused`."""
        if what == "moved":
            return what_moved(self)
        if of is not None:
            found = ONE[what](self.held, of)
            if found is None:
                raise missing()
            adjust = ADJUST[what](desk, self.held, of) if what in ADJUST else None
            more = {} if adjust is None else {"adjust": adjust}
            return {**found, **more, "flags": _flags_of(desk, self.held, what, of)}
        if what in READ:
            return READ[what](desk, self.held)
        if what in LOOKED_AT:
            return LOOKED_AT[what](desk, self, sent)
        return WRITE[what](desk, self.held, sent)


def open_panel(
    release: Path, searches: Path = preview.SEARCHES, before: Path | None = None
) -> Panel:
    """Read the release the panel shows, and the searches it ranks before and after a
    change. Where another release is named, what moved between it and the one that is
    shown is worked out. Raises `look.NotServed` and `preview.Unfit`."""
    root = Path(__file__).resolve().parents[3]
    held, ranked = look.open_held(release), preview.read_searches(searches, root)
    if before is None:
        return Panel(held, ranked)
    return Panel(held, ranked, moved_since(look.open_held(before), held, ranked, root))


def moved_since(before: Held, held: Held, searches: Sequence[Search], root: Path) -> dict[str, Any]:
    """What moved between a release and the one that is shown, as the step `moved` finds
    it: by the same function, from the receipts and the lists of this repository."""
    try:
        was, now = (between.with_its_lock(one.release, one.folder) for one in (before, held))
        folder = root / RECEIPTS_FOLDER
        receipts = [one for one in read_receipts(folder) if not one.made_up]
        lists = [load_list(path) for path in sorted(LISTS.glob("*.toml"))] if receipts else []
        return between.compare(was, now, receipts=receipts, lists=lists, searches=searches)
    except between.OtherCity:
        raise look.NotServed(OTHER_CITY) from None
    except (between.NoLock, LockError, ListError):
        raise look.NotServed(
            "The lock of a release, the receipts or the lists cannot be read, so what moved "
            "cannot be said"
        ) from None


def what_moved(panel: Panel) -> dict[str, Any]:
    """What moved between the release that was named beside it and the one that is shown."""
    if panel.moved is None:
        return {"moved": None, "says": NO_OTHER}
    # What each vibe of the release that is shown says of itself where it is a rough
    # guide, so that the screen says it beside the name of a vibe that came or moved.
    rough = {
        vibe.tag_id: told
        for vibe in panel.held.release.vibes
        if (told := look.rough_of(vibe)) is not None
    }
    return {"moved": panel.moved, "counts": between.counted(panel.moved), "rough": rough}


# What is kept


def _lines(desk: Desk) -> dict[str, tuple[Change, ...]]:
    try:
        return kept.read_all(desk.data)
    except kept.Unreadable as unreadable:
        desk.log(f"fault {unreadable}")
        raise Refused(
            server.HTTPStatus.INTERNAL_SERVER_ERROR, server.NOT_SAVED, UNREADABLE
        ) from None


def _about(held: Held, of: str) -> dict[str, Any]:
    """What a flag is of, in words: the area, and the measure or the vibe."""
    found = changes.flagged(of)
    if found is None:
        return {}
    kind, area_id, key = found
    area = held.areas.get(area_id)
    metric = held.metrics.get(cast(Any, key))
    vibe = held.vibes.get(cast(Any, key))
    label = metric.label if metric else vibe.label if vibe else key
    return {
        "kind": kind,
        "area_id": area_id,
        "area": None
        if area is None
        else {"id": area_id, "name": area.name, "borough": area.borough},
        "about": label,
        "key": key,
    }


def _flagged(desk: Desk, held: Held) -> list[dict[str, Any]]:
    """Every flag that stands, of every reviewer, newest first."""
    found = [
        {**kept.as_shown(line), **_about(held, line.of), "mine": reviewer == desk.reviewer}
        for reviewer, lines in _lines(desk).items()
        for line in changes.standing(lines)
        if line.what in (What.FLAG, What.LEAVE_OUT)
    ]
    return sorted(found, key=lambda one: (one["on"], one["n"]), reverse=True)


def _flags_of(desk: Desk, held: Held, what: str, of: str) -> list[dict[str, Any]]:
    """The flags that stand on what one screen shows: an area, a measure or a vibe."""
    if what == "area":
        return [one for one in _flagged(desk, held) if one.get("area_id") == of]
    return [one for one in _flagged(desk, held) if one.get("key") == of]


def flags(desk: Desk, held: Held) -> dict[str, Any]:
    return {"flags": _flagged(desk, held)}


def _is_held(held: Held, of: str) -> bool:
    """Whether the release holds what a flag names."""
    found = changes.flagged(of)
    if found is None or found[1] not in held.areas:
        return False
    kind, area_id, key = found
    if kind == changes.FIGURE:
        figure = held.release.feature(area_id, cast(Any, key)) if key in held.metrics else None
        cost = any(look.cost_key(c.tenure, c.segment) == key for c in held.costs.get(area_id, ()))
        return cost or (figure is not None and figure.value is not None)
    if kind == changes.BAND:
        return key in held.vibes
    return True


def _why(sent: Mapping[str, Any]) -> str:
    why = sent.get("why")
    if not isinstance(why, str) or not why.strip() or len(why) > changes.WHY_LIMIT:
        raise bad(NO_REASON)
    if not changes.plain(why):
        raise bad(NO_REASON)
    return why.strip()


def _add(desk: Desk, what: What, of: str, why: str, **more: Any) -> Change:
    try:
        return kept.add(
            desk.data, desk.reviewer, what, of, why=why, clock=desk.clock, keep=desk.keep, **more
        )
    except ChangesError:
        raise bad() from None
    except kept.Unreadable as unreadable:
        desk.log(f"fault {unreadable}")
        raise Refused(
            server.HTTPStatus.INTERNAL_SERVER_ERROR, server.NOT_SAVED, UNREADABLE
        ) from None


def flag(desk: Desk, held: Held, sent: object) -> dict[str, Any]:
    """Flag a figure, a band, a name or a border, with a note. It is a line like any other."""
    if not isinstance(sent, dict) or frozenset(cast(dict[str, Any], sent)) != FLAG:
        raise bad()
    body = cast(dict[str, Any], sent)
    of, leave_out = body["of"], body["leave_out"]
    if not isinstance(of, str) or type(leave_out) is not bool:
        raise bad()
    why = _why(body)
    if not _is_held(held, of):
        raise bad(NOT_HELD)
    if leave_out:
        # The file has a line for it, and no build applies one yet: a figure that is left
        # out needs a state of its own in the evidence. Until then nothing is kept that a
        # build would stop at.
        raise bad(NOT_YET_LEFT_OUT)
    what = What.FLAG
    with desk.lock:
        standing = kept.stands_for(_lines(desk), desk.reviewer)
        same = next((one for one in standing if one.key == (what, of) and one.why == why), None)
        # A flag given twice is written once.
        line = same or _add(desk, what, of, why)
    return {"line": kept.as_shown(line), "flags": _flagged(desk, held)}


# The history, and taking a line back


def _history(desk: Desk, held: Held) -> list[dict[str, Any]]:
    """Every line of every reviewer, newest first, with whether it stands."""
    found: list[dict[str, Any]] = []
    every = _lines(desk)
    for reviewer, lines in every.items():
        gone = changes.taken_back(lines)
        stands = {line.n for line in changes.standing(lines)}
        by = {line.takes_back: line.n for line in lines if line.takes_back and line.n not in gone}
        for line in lines:
            found.append(
                {
                    **kept.as_shown(line),
                    **_about(held, line.of),
                    "stands": line.n in stands,
                    "taken_back_by": by.get(line.n) if line.n in gone else None,
                    "mine": reviewer == desk.reviewer,
                }
            )
    return sorted(found, key=lambda one: (one["on"], one["n"]), reverse=True)


def history(desk: Desk, held: Held) -> dict[str, Any]:
    return {"history": _history(desk, held), "differ": differ(_lines(desk))}


def differ(every: Mapping[str, tuple[Change, ...]]) -> list[dict[str, Any]]:
    """Where two reviewers' changes to one thing differ: each is shown to the other.

    A flag is a reviewer's own, and two flags never differ. The founder's change is the
    one that is built.
    """
    stands = {
        reviewer: {line.key: line for line in changes.standing(lines)}
        for reviewer, lines in every.items()
    }
    found: list[dict[str, Any]] = []
    keys = sorted({key for held in stands.values() for key in held})
    for key in keys:
        if key[0] in (What.FLAG, What.LEAVE_OUT):
            continue
        said = {reviewer: held[key] for reviewer, held in stands.items() if key in held}
        if len({json.dumps(one.now, sort_keys=True) for one in said.values()}) > 1:
            found.append(
                {
                    "what": key[0].value,
                    "of": key[1],
                    "said": [kept.as_shown(line) for line in said.values()],
                    "built": records.FOUNDER if records.FOUNDER in said else None,
                }
            )
    return found


def take_back(desk: Desk, held: Held, sent: object) -> dict[str, Any]:
    """Take one line of the reviewer's own back, which is itself a line."""
    if not isinstance(sent, dict) or frozenset(cast(dict[str, Any], sent)) != TAKE_BACK:
        raise bad()
    body = cast(dict[str, Any], sent)
    n = body["n"]
    if type(n) is not int or n < 1:
        raise bad()
    why = _why(body)
    with desk.lock:
        mine = _lines(desk).get(desk.reviewer, ())
        named = mine[n - 1] if n <= len(mine) else None
        if named is None:
            raise bad(NOT_YOURS)
        if n in changes.taken_back(mine):
            raise bad(TAKEN_BACK)
        line = _add(desk, What.TAKE_BACK, named.of, why, takes_back=n)
    return {"line": kept.as_shown(line), "history": _history(desk, held)}


# To adjust, and to see what moves before anything is kept


def _mine(desk: Desk) -> tuple[Change, ...]:
    return _lines(desk).get(desk.reviewer, ())


def _refusal(error: ChangesError) -> Refused:
    return bad(BREAKS.get(error.rule))


def adjust_of(desk: Desk, held: Held, tag_id: str) -> dict[str, Any]:
    """What a person may adjust of a vibe, as it stands for them: the shares a slider
    starts from, and how far one may go."""
    core = tags_of(held.release.manifest.gritty_variant)
    try:
        standing = {vibe.tag_id: vibe for vibe in changes.adjusted(core, _mine(desk))}
    except ChangesError as error:
        raise _refusal(error) from None
    vibe = standing[TagId(tag_id)]
    served = held.vibes[vibe.tag_id]
    beside_residents = any(term.feature_id in COUNTS_RESIDENTS for term in vibe.terms)
    return {
        "shares": look.recipe_of(held, vibe),
        "least": 1,
        "most": PART_MAX_BESIDE_RESIDENTS if beside_residents else PART_MAX_HUNDREDTHS,
        "names": changes.names_of(vibe),
        "cannot_see": changes.lines_of(vibe),
        # Whether what stands for this reviewer is what the release carries.
        "as_served": vibe == served,
    }


# What a person may change, by the kind of line. `STANDS` says what stands of a thing for
# some lines, laid over core's own, which is what a change is made of. `MOVES` says what a
# change would move, where that can be worked out before a build.


def _vibe(held: Held, lines: Sequence[Change], of: str) -> Any:
    core = tags_of(held.release.manifest.gritty_variant)
    standing = {vibe.tag_id: vibe for vibe in changes.adjusted(core, lines)}
    if of not in TagId or TagId(of) not in standing:
        raise ChangesError(0, changes.NOT_CARRIED)
    return standing[TagId(of)]


def _measure(held: Held, lines: Sequence[Change], of: str) -> Any:
    if of not in FeatureId or FeatureId(of) not in held.metrics:
        raise ChangesError(0, changes.NOT_CARRIED)
    core = FEATURES[FeatureId(of)]
    named = held.metrics[FeatureId(of)].replace(label=core.label, short_label=core.short_label)
    return changes.relabelled([named], lines)[0]


def table_of(lines: Sequence[Change]) -> Table:
    """The table of tiers as it stands for some lines: the repository's, with what stands
    of them laid over it."""
    return changes.table_with(brand_table.the_table(), lines)


def _row(held: Held, lines: Sequence[Change], of: str) -> Any:
    found = table_of(lines).by_key.get(of)
    return None if found is None else changes.row_of(found)


STANDS: Final[Mapping[What, Callable[[Held, Sequence[Change], str], Any]]] = {
    What.RECIPE: lambda held, lines, of: changes.recipe_of(_vibe(held, lines, of)),
    What.NAME: lambda held, lines, of: changes.names_of(_vibe(held, lines, of)),
    What.CANNOT_SEE: lambda held, lines, of: changes.lines_of(_vibe(held, lines, of)),
    What.LABEL: lambda held, lines, of: changes.labels_of(_measure(held, lines, of)),
    What.BRAND: _row,
}


def worked_out_again(was: Any, now: Any, of: str) -> list[str]:
    """The measures a build works out again when a row of the table of tiers changes, by
    the label core gives each: the places and the nearest of each tier the chain is of or
    was of, the mix, and the nearest place of the chain where core names one."""
    rows = [row for row in (was, now) if row is not None]
    found = {
        of_a_tier(row["kind"], row["tier"], what) for row in rows for what in ("nearby", "distance")
    }
    chain = f"brand_{of}"
    named = {FeatureId(chain)} if chain in FeatureId else set[FeatureId]()
    every = sorted(found | named | {FeatureId.BRAND_MIX}, key=lambda feature: feature.value)
    return [FEATURES[feature].label for feature in every]


A_CHAIN_IS_SEEN: Final = (
    "A build adds a chain only where the file of places gives its name, as it is written "
    "here, to two places or more that stand apart. A name it gives to no place, or to one, "
    "is not shown to be a chain, and the build stops at the line."
)


def _moves(panel: Panel, lines: Sequence[Change], proposed: Change) -> dict[str, Any]:
    if proposed.what is What.RECIPE:
        return preview.of_a_recipe(panel.held, panel.searches, lines, proposed)
    if proposed.what is What.BRAND:
        again = {"worked_out_again": worked_out_again(proposed.was, proposed.now, proposed.of)}
        added = changes.added(brand_table.of_the_repository(), [*lines, proposed])
        return again | ({"needs": A_CHAIN_IS_SEEN} if proposed in added else {})
    return {}


def names_of_places(held: Held) -> frozenset[str]:
    """Every name of a place the release holds: of its areas, their boroughs and its places."""
    release = held.release
    return frozenset(
        {
            *(area.name for area in release.neighbourhoods),
            *(area.borough for area in release.neighbourhoods),
            *(alias for area in release.neighbourhoods for alias in area.aliases),
            *(place.name for place in release.places),
            *(alias for place in release.places for alias in place.aliases),
        }
    )


def _words_given(change: Change) -> list[str]:
    """Every word a line of a name, a label or of what a vibe cannot see gives."""
    now = cast(object, change.now)
    if isinstance(now, dict):
        return [held for held in cast(dict[str, object], now).values() if isinstance(held, str)]
    return [held for held in cast(list[object], now) if isinstance(held, str)]


def _checked(held: Held, lines: Sequence[Change]) -> None:
    """Hold some lines to everything a build would hold them to. Raises `ChangesError`.

    A build holds a name to the places of its release when it checks the
    release, at its end. The panel holds it to the places of the release it
    shows, so that nothing is kept that a build would stop at.
    """
    changes.adjusted(tags_of(held.release.manifest.gritty_variant), lines)
    changes.labels_hold(lines)
    changes.relabelled(held.release.metrics, lines)
    table_of(lines)
    names = names_of_places(held)
    for line in changes.standing(lines):
        if line.what in (What.NAME, What.CANNOT_SEE, What.LABEL) and any(
            holds_the_name_of_a_place(words, names) for words in _words_given(line)
        ):
            raise ChangesError(line.n, "names_name_no_place")


def relabel_of(desk: Desk, held: Held, feature_id: str) -> dict[str, Any]:
    """What a person may change of a measure, as it stands for them: its two labels. A
    measure that counts who lived somewhere keeps the name core gives it."""
    try:
        stands = _measure(held, _mine(desk), feature_id)
    except ChangesError as error:
        raise _refusal(error) from None
    served = held.metrics[stands.feature_id]
    return {
        "labels": changes.labels_of(stands),
        "may": stands.feature_id not in COUNTS_RESIDENTS,
        "as_served": changes.labels_of(stands) == changes.labels_of(served),
    }


ADJUST: Final[Mapping[str, Callable[[Desk, Held, str], dict[str, Any]]]] = {
    "vibe": lambda desk, held, of: adjust_of(desk, held, of),
    "measure": lambda desk, held, of: relabel_of(desk, held, of),
}


def _proposed(sent: object, fields: frozenset[str]) -> dict[str, Any]:
    if not isinstance(sent, dict) or frozenset(cast(dict[str, Any], sent)) != fields:
        raise bad()
    body = cast(dict[str, Any], sent)
    if not (isinstance(body["what"], str) and isinstance(body["of"], str)):
        raise bad()
    if body["what"] not in {what.value for what in STANDS}:
        raise bad()
    return body


def _previewed(desk: Desk, panel: Panel, body: Mapping[str, Any]) -> dict[str, Any]:
    what, of, now = What(body["what"]), cast(str, body["of"]), body["now"]
    mine = _mine(desk)
    try:
        was = STANDS[what](panel.held, mine, of)
        proposed = Change(
            n=len(mine) + 1,
            on=desk.clock().strftime(kept.DAY),
            by=desk.reviewer,
            what=what,
            of=of,
            was=was,
            now=now,
            why="-",
            takes_back=None,
        )
        rule = changes.broken(proposed)
        if rule is not None:
            raise ChangesError(0, rule)
        _checked(panel.held, [*mine, proposed])
        moves = _moves(panel, mine, proposed)
    except ChangesError as error:
        raise _refusal(error) from None
    seen = preview.seen(what.value, of, was, now)
    return {"what": what.value, "of": of, "was": was, "now": now, "seen": seen, **moves}


def look_first(desk: Desk, panel: Panel, sent: object) -> dict[str, Any]:
    """What a change would move, before it is kept. Nothing is written."""
    return _previewed(desk, panel, _proposed(sent, PREVIEW))


def keep(desk: Desk, panel: Panel, sent: object) -> dict[str, Any]:
    """Keep a change that was looked at, with its reason. It is a line of the file of
    changes, and changes nothing that is served until a build is made from the file."""
    body = _proposed(sent, KEEP)
    why = _why(body)
    with desk.lock:
        found = _previewed(desk, panel, body)
        if body["seen"] != found["seen"]:
            raise bad(NOT_LOOKED_AT)
        if json.dumps(found["was"], sort_keys=True) == json.dumps(found["now"], sort_keys=True):
            raise bad(NOTHING_CHANGED)
        line = _add(desk, What(body["what"]), body["of"], why, was=found["was"], now=found["now"])
    return {"line": kept.as_shown(line), "history": _history(desk, panel.held)}


# The table of brands

KINDS_SAID: Final = {"grocer": "Grocers", "gym": "Gyms", "coffee": "Coffee"}
TIERS_SAID: Final = {"premium": "Premium", "mid": "Mid-range", "value": "Value"}
ONLY_ONCE_BUILT: Final = (
    "What this moves is known only once it is built: the panel holds no file of places."
)


def brands(desk: Desk, held: Held) -> dict[str, Any]:
    """The table of tiers as it stands for the reviewer: the repository's, with what they
    kept laid over it. It names chains of shops, and no place."""
    of_the_file = brand_table.the_table()
    try:
        stands = table_of(_mine(desk))
    except ChangesError as error:
        raise _refusal(error) from None
    return {
        "kinds": [{"id": kind, "label": label} for kind, label in KINDS_SAID.items()],
        "tiers": [{"id": tier, "label": label} for tier, label in TIERS_SAID.items()],
        "read_in": of_the_file.read_in,
        "chains": [
            {
                "key": chain.key,
                **changes.row_of(chain),
                "on_the_founders_table": chain.on_the_founders_table,
                # Whether core names a measure of the chain: the distance to the nearest.
                "named_by_core": f"brand_{chain.key}" in FeatureId,
                "changed": of_the_file.by_key.get(chain.key) != chain,
            }
            for chain in stands.chains
        ],
        "taken_out": [
            {"key": chain.key, **changes.row_of(chain)}
            for chain in of_the_file.chains
            if chain.key not in stands.by_key
        ],
        "says": ONLY_ONCE_BUILT,
    }


def built_of(built_with: tuple[str, int] | None, content: bytes) -> int | None:
    """How many lines of the founder's file of changes the release was built with.

    A line is never changed and never removed, so the file a release was built with is
    the start of the file as it stands. Nought where the release was built with no file.
    None where it was built with a file that is not the start of this one.
    """
    if built_with is None:
        return 0
    sha256, size = built_with
    start = content[:size]
    if len(start) != size or hashlib.sha256(start).hexdigest() != sha256:
        return None
    return start.count(b"\n")


def not_yet_built(lines: Sequence[Change], built: int) -> list[Change]:
    """What stands of the founder's file that the release was not built with: what was
    changed since, and what was taken back since."""
    then = {line.key: line for line in changes.standing(lines[:built])}
    now = {line.key: line for line in changes.standing(lines)}
    since = [line for key, line in now.items() if then.get(key) != line]
    back = [
        line
        for line in lines[built:]
        if line.takes_back is not None
        and line.takes_back <= built
        and lines[line.takes_back - 1].key not in now
    ]
    return sorted([*since, *back], key=lambda line: line.n)


def home(desk: Desk, held: Held) -> dict[str, Any]:
    """What is served today, what waits for a person, and what was changed and not yet built."""
    queues = server.state(desk)["queues"]
    waiting = [
        {
            "queue": queue["queue"],
            "title": queue["title"],
            "left": cast(int, queue["total"]) - cast(int, queue["done"]),
            "total": queue["total"],
        }
        for queue in cast(list[dict[str, Any]], queues)
    ]
    founder = _lines(desk).get(records.FOUNDER, ())
    try:
        content = kept.path_of(desk.data, records.FOUNDER).read_bytes()
    except FileNotFoundError:
        content = b""
    built = built_of(held.built_with, content)
    return {
        "reviewer": desk.reviewer,
        "banner": server.BANNER[desk.synthetic],
        "served": look.served(held),
        "waiting": waiting,
        "flagged": len(_flagged(desk, held)),
        # How many lines of the founder's file the release was built with. None where it
        # was built with another file, and then every line that stands is listed.
        "built_with": built,
        "changed": [
            {**kept.as_shown(line), **_about(held, line.of)}
            for line in not_yet_built(founder, built or 0)
            if line.what is not What.FLAG
        ],
    }


def _of_the_release(
    read: Callable[[Held], dict[str, Any]],
) -> Callable[[Desk, Held], dict[str, Any]]:
    return lambda _, held: read(held)


READ: Final[Mapping[str, Callable[[Desk, Held], dict[str, Any]]]] = {
    "home": home,
    "areas": _of_the_release(look.areas),
    "outlines": _of_the_release(look.outlines),
    "measures": _of_the_release(look.measures),
    "flags": flags,
    "history": history,
    "brands": brands,
    "numbers": lambda desk, held: numbers.listed(),
}
ONE: Final[Mapping[str, Callable[[Held, str], dict[str, Any] | None]]] = {
    "area": look.area,
    "measure": look.measure,
    "vibe": look.vibe,
}
WRITE: Final[Mapping[str, Callable[[Desk, Held, object], dict[str, Any]]]] = {
    "flag": flag,
    "take-back": take_back,
}
LOOKED_AT: Final[Mapping[str, Callable[[Desk, Panel, object], dict[str, Any]]]] = {
    "preview": look_first,
    "keep": keep,
}
