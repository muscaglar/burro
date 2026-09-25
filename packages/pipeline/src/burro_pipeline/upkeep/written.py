"""What `moved` writes to a folder: what it found, whole, and as a page for a person.

What is written names areas, by the id and the name each bears in its release, and gives
figures of them. So it is written only where git takes nothing in, and nothing of it is
printed. `moved.json` is what was found, as the panel of the review desk reads it, and
`moved.md` says the same in tables.
"""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

JSON, PAGE = "moved.json", "moved.md"
NO_BAND = "no band"


def _number(value: float | None) -> str:
    """A figure as it is read: whole where it is whole, and with its places where not."""
    if value is None:
        return ""
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.4f}".rstrip("0")


def _table(head: Sequence[str], rows: Sequence[Sequence[object]], none: str) -> list[str]:
    if not rows:
        return [none, ""]
    cells = [[str(cell).replace("|", "/") for cell in row] for row in rows]
    return [
        f"| {' | '.join(head)} |",
        f"|{'|'.join('---' for _ in head)}|",
        *(f"| {' | '.join(row)} |" for row in cells),
        "",
    ]


def _area(one: Mapping[str, Any]) -> str:
    return f"{one['name']}, {one['borough']} ({one['id']})"


def _build(one: Mapping[str, Any]) -> list[object]:
    kind = "made up" if one["synthetic"] else "a preview" if one["preview"] else "finished"
    return [
        one["release_id"],
        one["built_at"],
        (one["commit"] or "")[:12],
        kind,
        one["areas"],
        one["measures"],
        one["vibes"],
    ]


def _steps(one: Mapping[str, Any]) -> list[object]:
    return [
        f"{one['changed']} of {one['areas']}",
        one["up"],
        one["down"],
        one["gained"],
        one["lost"],
        _number(one["middle"]),
        _number(one["most"]),
    ]


STEPS = ("Changed", "Up", "Down", "Gained a figure", "Lost its figure", "In the middle", "At most")


def _file(one: Mapping[str, Any]) -> list[object]:
    if "source" not in one:
        return ["", "", one["name"], "", "", ""]
    return [
        one["source"],
        one["list"] or "",
        one["item"] or "",
        one["edition"] or "",
        one["period"] or "",
        one["file_id"],
    ]


FILE = ("Source", "List", "Item", "Edition", "Period", "File")


def _measures(found: Mapping[str, Any]) -> list[str]:
    measures = found["measures"]
    said = [f"## Measures: {len(measures['moved'])} moved", ""]
    for how, words in (("came", "came"), ("went", "went")):
        rows = [[one["label"], one["id"], one["with_a_figure"]] for one in measures[how]]
        said += [f"### Measures that {words}: {len(rows)}", ""]
        said += _table(("Measure", "Id", "Areas with a figure"), rows, "None.")
    rows = [[one["label"], one["unit"], *_steps(one)] for one in measures["moved"]]
    said += ["### How far the figures moved", ""]
    said += _table(("Measure", "Unit", *STEPS), rows, "No figure of any measure changed.")
    for one in measures["moved"]:
        if one["dated"]["was"] != one["dated"]["now"]:
            said += [
                f"- {one['label']} was of {one['dated']['was']}, and is of {one['dated']['now']}."
            ]
    for one in measures["moved"]:
        most = [
            [_area(area), _number(area["was"]), _number(area["now"])] for area in one["moved_most"]
        ]
        if most:
            said += ["", f"### {one['label']}: the areas that moved most", ""]
            said += _table(("Area", "Was", "Is"), most, "")
    return said


def _vibes(found: Mapping[str, Any]) -> list[str]:
    vibes = found["vibes"]
    said = [f"## Vibes: {len(vibes['moved'])} moved", ""]
    for how in ("came", "went"):
        rows = [[one["label"], one["id"]] for one in vibes[how]]
        said += [f"### Vibes that {how}: {len(rows)}", ""]
        said += _table(("Vibe", "Id"), rows, "None.")
    rows = [
        [
            one["label"],
            f"{one['changed']} of {one['areas']}",
            one["up"],
            one["down"],
            one["gained"],
            one["lost"],
            ", ".join(f"{step['areas']} by {step['by']:+d}" for step in one["by_bands"]),
            "yes" if one["recipe_changed"] else "",
        ]
        for one in vibes["moved"]
    ]
    head = (
        "Vibe",
        "Changed band",
        "Up",
        "Down",
        "Gained a band",
        "Lost its band",
        "By how many bands",
        "Its recipe or name changed",
    )
    said += ["### How many areas changed band", ""]
    said += _table(head, rows, "No area changed band on any vibe.")
    for one in vibes["moved"]:
        most = [[_area(area), area["was"], area["now"]] for area in one["moved_most"]]
        if most:
            said += [f"### {one['label']}: the areas that moved most", ""]
            said += _table(("Area", "Was in band", "Is in band"), most, "")
    return said


def _searches(found: Mapping[str, Any]) -> list[str]:
    said = [f"## The first ten areas of {len(found['searches'])} searches", ""]
    for one in found["searches"]:
        was, now = one["before"], one["after"]
        same = (
            "the same, in the same order"
            if one["same"]
            else (
                f"not the same: {one['kept']} stayed, {one['came']} came, {one['went']} went, "
                f"and {one['reordered']} of those that stayed stand at another place"
            )
        )
        said += [f"### {one['name']}", "", one["read_as"], ""]
        said += [f"- {words}" for words in dict.fromkeys([*was["notes"], *now["notes"]])]
        said += [
            f"- Before, {was['ranked']} areas were ranked and {was['left_out']} left out by a "
            f"firm limit. After, {now['ranked']} and {now['left_out']}.",
            f"- The first ten are {same}.",
            "",
        ]
        rows = [
            [
                at + 1,
                _area(was["first"][at]) if at < len(was["first"]) else "",
                _area(now["first"][at]) if at < len(now["first"]) else "",
            ]
            for at in range(max(len(was["first"]), len(now["first"])))
        ]
        said += _table(("Place", "Before", "After"), rows, "No area is ranked.")
    return said


def page(found: Mapping[str, Any]) -> str:
    """What moved, as a page a person reads before they approve a build."""
    before, after, areas, files = found["before"], found["after"], found["areas"], found["files"]
    said = [
        f"# What moved between {before['release_id']} and {after['release_id']}",
        "",
        "Made by the step `moved`. It names areas and gives figures of them, so it is never "
        "committed.",
        "",
    ]
    head = ("Release", "Built at", "Commit", "Kind", "Areas", "Measures", "Vibes")
    said += _table(head, [_build(before), _build(after)], "")
    said += [f"## Areas: {len(areas['came'])} came, {len(areas['went'])} went", ""]
    for how in ("came", "went", "redrawn"):
        said += [
            f"### Areas that {'were ' if how == 'redrawn' else ''}{how}: {len(areas[how])}",
            "",
        ]
        said += _table(("Area",), [[_area(one)] for one in areas[how]], "None.")
    said += [f"### Areas that bear another name: {len(areas['renamed'])}", ""]
    rows = [[f"{one['was']}, {one['was_in']}", _area(one)] for one in areas["renamed"]]
    said += _table(("Was", "Is"), rows, "None.")
    said += ["### The areas that moved most, of all", ""]
    rows = [[_area(one), one["bands"], one["vibes"], one["figures"]] for one in areas["moved_most"]]
    head = ("Area", "Bands it moved by, in all", "Vibes it changed band on", "Figures that changed")
    said += _table(head, rows, "No area moved.")
    said += _measures(found) + _vibes(found)
    said += [f"## What a home sells for: {len(found['costs'])} kinds of home moved", ""]
    rows = [[f"{one['segment']} to {one['tenure']}", *_steps(one)] for one in found["costs"]]
    said += _table(("Home", *STEPS), rows, "No price changed.")
    said += ["## The files behind the builds", ""]
    if not files["compared"]:
        said += ["A made-up release has no lock, so no file was compared.", ""]
    said += [f"{files['same']} inputs are the same file in both.", ""]
    rows = [
        [*_file(one["was"])[:5], _file(one["now"])[3], _file(one["now"])[4]]
        for one in files["changed"]
    ]
    head = (*FILE[:3], "Edition before", "Period before", "Edition after", "Period after")
    said += [f"### Files that changed: {len(rows)}", "", *_table(head, rows, "None.")]
    for how in ("came", "went"):
        rows = [_file(one) for one in files[how]]
        said += [f"### Files that {how}: {len(rows)}", "", *_table(FILE, rows, "None.")]
    return "\n".join(said + _searches(found)).rstrip("\n") + "\n"


def write(found: Mapping[str, Any], folder: Path) -> tuple[Path, Path]:
    """Write what was found to a folder: whole, and as a page. Gives back the two files."""
    folder.mkdir(parents=True, exist_ok=True)
    whole, words = folder / JSON, folder / PAGE
    whole.write_text(
        json.dumps(found, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    words.write_text(page(found), encoding="utf-8")
    return whole, words
