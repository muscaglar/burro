"""The travel design and the package's guide, held to the code they describe.

A page goes stale without a sound. Each test here reads a page and fails when
it names something that is no longer there.
"""

import ast
import re
from pathlib import Path

import burro_pipeline.travel
from burro_pipeline.travel.engine import Settings
from burro_pipeline.travel.made_up import RELEASE_ID

REPOSITORY = Path(__file__).parents[4]
DESIGN = (REPOSITORY / "docs" / "design" / "london-data-travel.md").read_text(encoding="utf-8")
GUIDE = (REPOSITORY / "packages" / "pipeline" / "AGENTS.md").read_text(encoding="utf-8")
CONTRACT = (REPOSITORY / "docs" / "design" / "contract.md").read_text(encoding="utf-8")
SOURCE = Path(burro_pipeline.travel.__file__).parent
TESTS = Path(__file__).parent


def every_test() -> set[str]:
    found: set[str] = set()
    for module in sorted(TESTS.glob("test_*.py")):
        tree = ast.parse(module.read_text(encoding="utf-8"))
        found |= {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    return found


def test_every_test_the_design_names_is_a_test_there_is():
    named = set(re.findall(r"`(test_[a-z0-9_]+)`", DESIGN))

    assert len(named) >= 7
    assert named <= every_test()


def test_every_module_the_design_and_the_guide_name_is_a_module_there_is():
    modules = {path.name for path in SOURCE.glob("*.py")} - {"__init__.py"}
    in_the_design = set(re.findall(r"^\| `([a-z_]+\.py)` \|", DESIGN, re.MULTILINE))
    in_the_guide = set(re.findall(r"`travel/([a-z_]+\.py)`", GUIDE))
    in_the_package = set(
        re.findall(r"^\| `([a-z_]+)` \|", burro_pipeline.travel.__doc__ or "", re.M)
    )

    assert in_the_design == modules
    assert in_the_guide <= modules
    assert {f"{name}.py" for name in in_the_package} == modules


def test_the_settings_the_design_gives_are_the_settings_of_the_step():
    settings = Settings()
    said = " ".join(DESIGN.split())

    assert "| Window | Every departure minute from 07:00 to 08:59: 120 of them |" in said
    assert "| Cutoff | Public transport 120 minutes. Bike 60. Foot 60 |" in said
    assert "| Walking | 4.8 km/h |" in said and "| Cycling | 15 km/h" in said
    assert "| `pt_typical` | 50th |" in said and "| `pt_just_missed` | 90th |" in said
    assert "`Settings` gives 60 seconds, 2,400 metres and 800 metres" in said
    assert (settings.board_slack, settings.longest_walk, settings.longest_change) == (60, 2400, 800)
    assert (settings.departures, settings.cutoff_pt, settings.walk_speed) == (120, 120, 4800)


def test_the_release_that_is_built_on_demand_is_named_where_it_is_described():
    assert f"`{RELEASE_ID}`" in CONTRACT and f"`{RELEASE_ID}`" in GUIDE


def test_no_module_of_travel_reads_the_environment_or_a_clock():
    """The step is told nothing but its arguments, and the same arguments give the same bytes."""
    for module in sorted(SOURCE.glob("*.py")):
        tree = ast.parse(module.read_text(encoding="utf-8"))
        imported = {
            alias.name if isinstance(node, ast.Import) else node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.Import | ast.ImportFrom)
            for alias in node.names
        }
        named = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        assert not imported & {"os", "time", "random", "secrets", "uuid", "getpass"}, module.name
        assert not named & {"environ", "getenv", "now", "today", "utcnow"}, module.name
