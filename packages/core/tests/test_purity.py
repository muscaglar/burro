import ast
from pathlib import Path

import burro_core
import pytest

SOURCE = Path(burro_core.__file__).parent
MODULES = sorted(SOURCE.glob("*.py"))

# Everything core may import. Each is arithmetic, text or typing: none can open
# a file, read the clock, the environment or a random source, or reach a network.
ALLOWED = {
    "bisect",
    "collections.abc",
    "dataclasses",
    "enum",
    "hashlib",
    "itertools",
    "json",
    "math",
    "re",
    "types",
    "typing",
    "unicodedata",
    "pydantic",
}
# Builtins that do IO, or run code that could. None may be called or even named.
FORBIDDEN_NAMES = {"open", "print", "input", "eval", "exec", "compile", "breakpoint", "__import__"}
THE_MODULES = {
    "ids",
    "catalogue",
    "release",
    "spec",
    "ops",
    "reducer",
    "rank",
    "estimate",
    "places",
    "likeness",
    "facts",
    "portrait",
    "explain",
    "verify",
    "interpret",
    # The rule-based reader: its words, how it reads a text, and what is plain.
    "vocabulary",
    "lexicon",
    "reading",
    "grammar",
    # The census of an area's page. Nothing above imports it: `test_census.py` holds that.
    "census",
    # Household income, shown on an area's page as the census is. Nothing above imports
    # it either: `test_income.py` holds that.
    "income",
}


def imported(tree: ast.AST) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "core imports by full name"
            found.add(node.module or "")
    return found


def test_core_holds_the_modules_the_contract_names():
    names = {path.stem for path in MODULES if not path.stem.startswith("_")}
    assert names == THE_MODULES
    assert not [path for path in SOURCE.iterdir() if path.is_dir() and path.name != "__pycache__"]


@pytest.mark.parametrize("path", MODULES, ids=[path.stem for path in MODULES])
def test_core_imports_nothing_that_does_io(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    outside = {name for name in imported(tree) if not name.startswith("burro_core")}
    assert outside <= ALLOWED, sorted(outside - ALLOWED)

    named = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    assert not named & FORBIDDEN_NAMES, sorted(named & FORBIDDEN_NAMES)


def test_core_depends_on_pydantic_only():
    manifest = (SOURCE.parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    dependencies = manifest.split("dependencies = [")[1].split("]")[0]
    assert [line.strip() for line in dependencies.strip().splitlines()] == ['"pydantic>=2.9",']


def test_the_engine_names_its_version():
    assert burro_core.ENGINE_VERSION == "1.14.0"
    assert burro_core.CATALOGUE_VERSION == 14
    assert set(burro_core.__all__) <= set(dir(burro_core))
