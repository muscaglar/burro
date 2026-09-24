"""What is built and not needed yet is kept where nobody builds on it by mistake.

The examples of the records are part of the tests, and of no package. The
claim waits for the milestone on quotations, and says so where a reader meets
it first: at the head of its module, and in the README.
"""

import ast
from functools import cache
from pathlib import Path

from burro_pipeline import evidence as package

PACKAGE = Path(package.__file__).parent
REPOSITORY = Path(__file__).parents[4]
# Every module that is shipped: the pipeline, core and the API.
SHIPPED = sorted(
    path
    for folder in ("packages", "services")
    for path in (REPOSITORY / folder).glob("*/src/**/*.py")
)
NOT_YET_USED = (
    "Not yet used. It waits for milestone M8, on quotations: build nothing on it until then."
)
# The names the claim's module gives. One of them imported is the claim built upon.
OF_THE_CLAIM = {
    "Claim",
    "ClaimKind",
    "Derived",
    "FoundBy",
    "Review",
    "ReviewStatus",
    "Reviewer",
    "claim_id_of",
    "text_sha256",
}
# The modules that hold the claim today: the record of a release, which keeps a list of
# claims, the report, which counts them, and the package, which gives their names.
HOLD_THE_CLAIM = {
    f"packages/pipeline/src/burro_pipeline/evidence/{name}"
    for name in ("__init__.py", "coverage.py", "store.py")
}


@cache
def imported(path: Path) -> frozenset[str]:
    """Every name a module imports, as `module` and as `module.name`. Each module is read once."""
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            found.add(node.module or "")
            found |= {f"{node.module}.{alias.name}" for alias in node.names}
    return frozenset(found)


def test_there_is_something_to_read():
    assert len(SHIPPED) > 40
    assert PACKAGE / "claim.py" in SHIPPED


def test_the_examples_are_part_of_the_tests_and_of_no_package():
    assert not (PACKAGE / "examples.py").exists()
    assert (Path(__file__).parent / "examples.py").is_file()
    importers = [
        path.relative_to(REPOSITORY).as_posix()
        for path in SHIPPED
        if any(name.split(".")[-1] == "examples" for name in imported(path))
    ]
    assert importers == []


def test_the_claim_says_at_its_head_that_it_is_not_yet_used():
    tree = ast.parse((PACKAGE / "claim.py").read_text(encoding="utf-8"))
    said = ast.get_docstring(tree) or ""
    assert said.splitlines()[0] == NOT_YET_USED


def test_the_readme_says_that_the_claim_is_not_yet_used():
    readme = (PACKAGE / "README.md").read_text(encoding="utf-8")
    assert NOT_YET_USED in readme
    # It is said where the record is first named, and again where it is described.
    assert readme.count(NOT_YET_USED) == 2


def test_nothing_is_built_on_the_claim_before_its_milestone():
    """A module that comes to import the claim fails here, until milestone M8 changes this."""
    builds_on_it = {
        path.relative_to(REPOSITORY).as_posix()
        for path in SHIPPED
        if path != PACKAGE / "claim.py"
        and any(
            name == "burro_pipeline.evidence.claim"
            or (name.startswith("burro_pipeline.evidence") and name.split(".")[-1] in OF_THE_CLAIM)
            for name in imported(path)
        )
    }
    assert builds_on_it == HOLD_THE_CLAIM
