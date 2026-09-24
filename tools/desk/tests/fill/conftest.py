"""What the tests of the fill step share: the made-up city, filled once.

Every test runs offline, on the synthetic release or on a small draft it writes itself.
No real file is read: a draft that names real sources is the made-up city under other
names, and it never leaves the folder of the test.
"""

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from desk import fill
from desk.fill import synthetic

ROOT = Path(__file__).resolve().parents[4]
RELEASE = ROOT / "data" / "fixtures" / "synthetic"
REGISTRY = ROOT / "registry" / "sources"

# The sources a draft of London would name, in place of those of the made-up city. Each is
# registered for the use its file is read under.
AS_IF_REAL = (
    ("synthetic-names", "os-open-names"),
    ("synthetic-items", "wikidata-places-and-landmarks"),
    ("synthetic-centres", "gla-town-centre-boundaries"),
    ("synthetic-wards", "os-boundary-line"),
)
REAL_SOURCE = {
    "kinds.csv": "overture-places",
    "figures.csv": "defra-pcm-background-air",
    "claims.jsonl": "wikimedia-wikipedia-excerpts",
}
CELLS_SOURCE = "ons-output-areas-2021"


@dataclass(frozen=True)
class Filled:
    data: Path
    report: fill.Report

    def rows(self, queue: str) -> list[dict[str, Any]]:
        text = (self.data / "items" / f"{queue}.jsonl").read_text(encoding="utf-8")
        return [json.loads(line) for line in text.splitlines()]

    def header(self, queue: str) -> dict[str, Any]:
        return self.rows(queue)[0]

    def items(self, queue: str) -> list[dict[str, Any]]:
        return self.rows(queue)[1:]

    def item(self, queue: str, name: str) -> dict[str, Any]:
        return next(item for item in self.items(queue) if item["id"] == name)

    def ids(self, queue: str) -> list[str]:
        return [item["id"] for item in self.items(queue)]

    def layer(self, group: str, layer: str) -> dict[str, Any]:
        path = self.data / "layers" / group / f"{layer}.geojson"
        return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def drafted(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The draft of the made-up city. Made once: no test may write to it."""
    folder = tmp_path_factory.mktemp("desk-draft")
    synthetic.make(RELEASE, folder)
    return folder


def fill_made_up(data: Path) -> Filled:
    return Filled(data, fill.fill(RELEASE, data, synthetic=True))


@pytest.fixture(scope="session")
def made_up(tmp_path_factory: pytest.TempPathFactory) -> Filled:
    """The queues of the made-up city. Filled once: no test may write to it."""
    return fill_made_up(tmp_path_factory.mktemp("desk-synthetic"))


def as_if_real(made_up_draft: Path, folder: Path) -> Path:
    """A draft that names real sources and real ids, made from the draft of the made-up city."""
    shutil.copytree(made_up_draft, folder)
    for path in sorted(each for each in folder.rglob("*") if each.is_file()):
        text = path.read_text(encoding="utf-8").replace("syn-", "lon-")
        for made_up_source, real in AS_IF_REAL:
            text = text.replace(made_up_source, real)
        # The member that says which city a layer is of keeps its name, and says London.
        text = text.replace('"synthetic":true', '"\x00":false')
        text = text.replace("synthetic", REAL_SOURCE.get(path.name, CELLS_SOURCE))
        path.write_text(text.replace("\x00", "synthetic"), encoding="utf-8")
    return folder


@pytest.fixture
def real_draft(made_up: Filled, tmp_path: Path) -> Path:
    return as_if_real(made_up.data / "draft", tmp_path / "desk" / "draft")
