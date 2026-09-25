"""Every guide can be found, every link leads somewhere, and every picture is drawn.

The guides were written piece by piece, and a guide that nothing links to is read by
nobody. So docs/README.md is the one way in, and each test here holds the guides to it:

1. Every guide under docs/ and deploy/ is reached from it in two steps at most. A step
   is a link from one guide to another.
2. Every link of a guide that points into the repository points at a file that is there,
   and at a heading that is there where it names one.
3. Every picture is a Mermaid block of a kind GitHub draws, short enough to read.

Each rule is tried as well on made-up guides that break it, so that a rule that finds
nothing is seen to find nothing. The real guides hold hundreds of links to the web and of
blocks that are no picture, and come out clean: that is the test of both. Standard
library only.
"""

import re
from pathlib import Path
from urllib.parse import unquote

import pytest

ROOT = Path(__file__).resolve().parents[2]
# The one way in, and how far from it a guide may be.
WAY_IN = Path("docs/README.md")
STEPS = 2
# Where the guides are. Every one of them must be found.
FOLDERS = ("docs", "deploy")
# The pages at the top that lead a reader in. Their links are held as a guide's are.
AT_THE_TOP = ("README.md", "AGENTS.md")

# The kinds of picture GitHub draws from a block marked `mermaid`.
KINDS = frozenset(
    {
        *("flowchart", "graph", "sequenceDiagram", "classDiagram", "stateDiagram"),
        *("stateDiagram-v2", "erDiagram", "gantt", "pie", "journey", "gitGraph"),
    }
)
# A picture longer than this, or of more boxes, is not read at a glance.
LINES = 30
BOXES = 12

FENCE = re.compile(r"^\s*(```+|~~~+)\s*([A-Za-z0-9_-]*)")
CODE = re.compile(r"`[^`\n]*`")
LINK = re.compile(r"(?<!!)\[(?:[^\]\[]|\[[^\]]*\])*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
ELSEWHERE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
BOX = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*[\[({>]")


def guides(root: Path) -> list[Path]:
    """Every guide there is, by its path from the top of the repository."""
    found = [
        page.relative_to(root)
        for folder in FOLDERS
        for page in sorted((root / folder).rglob("*.md"))
    ]
    return [page for page in found if "node_modules" not in page.parts]


def parts(text: str) -> tuple[list[tuple[int, str]], list[tuple[int, str, list[str]]]]:
    """The lines of a guide that are prose, and each fenced block with what it is marked as.

    A link or a heading inside a block is an example, and leads nowhere.
    """
    prose: list[tuple[int, str]] = []
    blocks: list[tuple[int, str, list[str]]] = []
    fence = ""
    for number, line in enumerate(text.splitlines(), 1):
        opened = FENCE.match(line)
        if fence:
            if opened and opened[1].startswith(fence) and not opened[2]:
                fence = ""
            else:
                blocks[-1][2].append(line)
        elif opened:
            fence = opened[1]
            blocks.append((number, opened[2], []))
        else:
            prose.append((number, line))
    return prose, blocks


def links(text: str) -> list[tuple[int, str]]:
    """Every link of a guide that points into the repository, with the line it stands on."""
    prose, _ = parts(text)
    return [
        (number, found[1])
        for number, line in prose
        for found in LINK.finditer(CODE.sub("", line))
        if not ELSEWHERE.match(found[1])
    ]


def named_by(heading: str) -> str:
    """The name GitHub gives a heading, which a link names after `#`."""
    plain = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading)
    plain = plain.replace("`", "").replace("*", "").strip().lower()
    return re.sub(r"[^\w\- ]", "", plain).replace(" ", "-")


def headings(text: str) -> set[str]:
    """Every name a link may give after `#` to reach a heading of a guide."""
    prose, _ = parts(text)
    seen: dict[str, int] = {}
    found: set[str] = set()
    for _, line in prose:
        heading = HEADING.match(line)
        if heading is None:
            continue
        name = named_by(heading[2])
        found.add(name if name not in seen else f"{name}-{seen[name]}")
        seen[name] = seen.get(name, 0) + 1
    return found


def pointed_at(page: Path, target: str) -> tuple[Path, str]:
    """The path a link points at, from the top of the repository, and the heading it names."""
    path, _, heading = target.partition("#")
    if not path:
        return page, heading
    start = Path() if path.startswith("/") else page.parent
    # Put together by its parts, so that `..` climbs and nothing is asked of the disk.
    at: list[str] = []
    for part in (*start.parts, *Path(unquote(path).lstrip("/")).parts):
        if part == "..":
            if not at:
                return Path(".."), heading
            at.pop()
        elif part != ".":
            at.append(part)
    return Path(*at), heading


def leads_nowhere(root: Path, pages: list[Path]) -> list[str]:
    """Every link of these pages that points at nothing, with where it stands."""
    found: list[str] = []
    for page in pages:
        for number, target in links((root / page).read_text(encoding="utf-8")):
            path, heading = pointed_at(page, target)
            if path.parts[:1] == ("..",) or not (root / path).exists():
                found.append(f"{page}:{number}: {target} points at no file")
            elif heading and path.suffix == ".md":
                there = headings((root / path).read_text(encoding="utf-8"))
                if heading.lower() not in there:
                    found.append(f"{page}:{number}: {target} points at no heading")
    return found


def reached(root: Path, way_in: Path, steps: int) -> set[Path]:
    """Every guide that is reached from the way in, in so many steps at most."""
    found = {way_in}
    edge = {way_in}
    for _ in range(steps):
        beyond: set[Path] = set()
        for page in sorted(edge):
            for _, target in links((root / page).read_text(encoding="utf-8")):
                path, _ = pointed_at(page, target)
                if path.suffix == ".md" and (root / path).is_file() and path not in found:
                    beyond.add(path)
        found |= beyond
        edge = beyond
    return found


def not_found(root: Path, way_in: Path = WAY_IN, steps: int = STEPS) -> list[str]:
    """Every guide that a reader who starts at the way in does not reach."""
    within = reached(root, way_in, steps)
    return [str(page) for page in guides(root) if page not in within]


def not_drawn(root: Path, pages: list[Path]) -> list[str]:
    """Every picture that GitHub would not draw, or that is too long to read."""
    found: list[str] = []
    for page in pages:
        _, blocks = parts((root / page).read_text(encoding="utf-8"))
        for number, marked, lines in blocks:
            if marked != "mermaid":
                continue
            held = [line for line in lines if line.strip()]
            kind = held[0].split()[0] if held else ""
            boxes = {box[1] for line in held[1:] if (box := BOX.match(line))}
            if kind not in KINDS:
                found.append(f"{page}:{number}: a picture of a kind that is not drawn: {kind!r}")
            if len(held) > LINES:
                found.append(f"{page}:{number}: a picture of {len(held)} lines, over {LINES}")
            if len(boxes) > BOXES:
                found.append(f"{page}:{number}: a picture of {len(boxes)} boxes, over {BOXES}")
    return found


# The guides as they are


def test_there_are_guides_and_the_way_in_is_one_of_them():
    found = guides(ROOT)
    assert len(found) > 100
    assert WAY_IN in found
    assert {Path("deploy/README.md"), Path("docs/adr/README.md")} <= set(found)


def test_every_guide_is_reached_from_the_way_in_in_two_steps():
    lost = not_found(ROOT)
    assert lost == [], f"link each from {WAY_IN}, or from a page that {WAY_IN} links to"


def test_every_link_into_the_repository_points_at_a_file_that_is_there():
    pages = [*guides(ROOT), *(Path(name) for name in AT_THE_TOP)]
    assert sum(len(links((ROOT / page).read_text(encoding="utf-8"))) for page in pages) > 500
    assert leads_nowhere(ROOT, pages) == []


def test_every_picture_is_of_a_kind_that_is_drawn_and_is_short_enough_to_read():
    pages = guides(ROOT)
    pictures = [
        block
        for page in pages
        for block in parts((ROOT / page).read_text(encoding="utf-8"))[1]
        if block[1] == "mermaid"
    ]
    assert len(pictures) >= 4, "the picture of the whole has four"
    assert not_drawn(ROOT, pages) == []


def test_the_way_in_names_every_design_and_every_decision_record_itself():
    """Each is one step away, so that none is found only through another."""
    near = reached(ROOT, WAY_IN, 1)
    own = [page for page in guides(ROOT) if page.parts[:2] in (("docs", "design"), ("docs", "adr"))]
    assert len(own) > 50
    assert [str(page) for page in own if page not in near] == []


# The rules, tried on guides that break them


def write(root: Path, pages: dict[str, str]) -> Path:
    for name, text in pages.items():
        page = root / name
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(text, encoding="utf-8")
    return root


MADE_UP = {
    "docs/README.md": "# Where to look\n\n[One](one.md), and [the desk](../deploy/README.md).\n",
    "docs/one.md": "# One\n\n## A part of it\n\n[Two](deep/two.md).\n",
    "docs/deep/two.md": "# Two\n\n[Back](../one.md#a-part-of-it), and [up](../README.md).\n",
    "deploy/README.md": "# The desk\n\n[The way in](../docs/README.md).\n",
}


def test_made_up_guides_that_keep_every_rule_are_found_whole(tmp_path: Path):
    root = write(tmp_path, MADE_UP)
    assert not_found(root) == []
    assert leads_nowhere(root, guides(root)) == []
    assert not_drawn(root, guides(root)) == []


def test_a_guide_that_nothing_links_to_is_not_found(tmp_path: Path):
    root = write(tmp_path, {**MADE_UP, "docs/orphan.md": "# Nobody links here\n"})
    assert not_found(root) == ["docs/orphan.md"]


def test_a_guide_three_steps_from_the_way_in_is_not_found(tmp_path: Path):
    far = {"docs/deep/two.md": "# Two\n\n[Three](three.md).\n", "docs/deep/three.md": "# Three\n"}
    root = write(tmp_path, {**MADE_UP, **far})
    assert not_found(root) == ["docs/deep/three.md"]
    assert not_found(root, steps=3) == []


def test_a_guide_named_only_in_code_or_by_its_folder_is_not_found(tmp_path: Path):
    named = "# One\n\n`[Two](deep/two.md)`, and [its folder](deep/).\n"
    named += "\n```\n[Two](deep/two.md)\n```\n"
    root = write(tmp_path, {**MADE_UP, "docs/one.md": named})
    assert not_found(root) == ["docs/deep/two.md"]


def test_a_link_to_a_file_that_is_not_there_is_found(tmp_path: Path):
    root = write(tmp_path, {**MADE_UP, "docs/one.md": "# One\n\n[Gone](deep/gone.md).\n"})
    assert leads_nowhere(root, guides(root)) == [
        "docs/deep/two.md:3: ../one.md#a-part-of-it points at no heading",
        "docs/one.md:3: deep/gone.md points at no file",
    ]


def test_a_link_that_climbs_out_of_the_repository_is_found(tmp_path: Path):
    root = write(tmp_path / "top", {**MADE_UP, "docs/one.md": "# One\n\n[Out](../../out.md).\n"})
    (tmp_path / "out.md").write_text("# Outside\n", encoding="utf-8")
    assert "docs/one.md:3: ../../out.md points at no file" in leads_nowhere(root, guides(root))


def test_a_link_to_a_heading_that_is_not_there_is_found(tmp_path: Path):
    renamed = "# One\n\n## Another part\n\n[Two](deep/two.md).\n"
    root = write(tmp_path, {**MADE_UP, "docs/one.md": renamed})
    assert leads_nowhere(root, guides(root)) == [
        "docs/deep/two.md:3: ../one.md#a-part-of-it points at no heading"
    ]


@pytest.mark.parametrize(
    ("heading", "name"),
    [
        ("London, from the bucket to the service", "london-from-the-bucket-to-the-service"),
        ("6. Read the lock, and approve the release", "6-read-the-lock-and-approve-the-release"),
        ("The designs, under `design/`", "the-designs-under-design"),
        ("What [the plan](PLAN.md) says", "what-the-plan-says"),
    ],
)
def test_a_heading_is_named_as_github_names_it(heading: str, name: str):
    assert named_by(heading) == name


def test_a_heading_that_stands_twice_is_named_apart_the_second_time():
    assert headings("# What\n\n## Not checked\n\ntext\n\n### Not checked\n") == {
        "what",
        "not-checked",
        "not-checked-1",
    }


def picture(*lines: str) -> str:
    return "# Drawn\n\n```mermaid\n" + "\n".join(lines) + "\n```\n"


@pytest.mark.parametrize(
    ("drawn", "fault"),
    [
        (picture("flowchart LR", '    a["One"] --> b["Two"]'), None),
        (picture("sequenceDiagram", "    A->>B: asks"), None),
        (picture("zenuml", "    A.b()"), "of a kind that is not drawn"),
        (picture("flowchart TD", *(f"    a{n} --> b{n}" for n in range(LINES))), "lines, over"),
        (picture("flowchart TD", *(f'    a{n}["Box"]' for n in range(BOXES + 1))), "boxes, over"),
        (picture(), "of a kind that is not drawn"),
    ],
)
def test_a_picture_is_held_to_its_kind_and_its_size(tmp_path: Path, drawn: str, fault: str | None):
    root = write(tmp_path, {**MADE_UP, "docs/one.md": drawn + "\n## A part of it\n"})
    found = not_drawn(root, guides(root))
    assert (found == []) if fault is None else (len(found) == 1 and fault in found[0])
