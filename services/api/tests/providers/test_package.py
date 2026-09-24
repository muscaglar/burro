"""What the package may be made of: the standard library, and nothing of a provider's."""

import ast
import subprocess
import sys
from pathlib import Path

import pytest
from burro_api import providers

SOURCE = Path(providers.__file__).parent
MODULES = sorted(SOURCE.glob("*.py"))
# What a module may import as it is loaded, beside the standard library.
OURS = ("burro_api.providers", "burro_api.logs")
# What one module may import when it is asked for a reader, and no sooner.
WHEN_ASKED = {"measure.py": {"burro_api.reader", "burro_core.interpret"}}


def imports_of(path: Path) -> list[tuple[str, bool]]:
    """Each module a file imports, and whether it does so as the file is loaded."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    at_the_top = {id(node) for node in tree.body}
    found: list[tuple[str, bool]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [(alias.name, id(node) in at_the_top) for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, f"{path.name} imports by where it stands"
            # `from burro_api import logs` is an import of `burro_api.logs`.
            whole = [f"{node.module}.{alias.name}" for alias in node.names]
            named = whole if node.module == "burro_api" else [node.module or ""]
            found += [(name, id(node) in at_the_top) for name in named]
    return found


def test_the_package_is_the_modules_the_design_names():
    assert [module.name for module in MODULES] == [
        "__init__.py",
        "anthropic.py",
        "base.py",
        "choose.py",
        "deepseek.py",
        "gemini.py",
        "interface.py",
        "measure.py",
        "openai.py",
        "terms.py",
    ]


@pytest.mark.parametrize("module", MODULES, ids=lambda module: module.name)
def test_a_module_imports_the_standard_library_and_its_own_package_and_no_more(module: Path):
    for name, at_the_top in imports_of(module):
        if name.split(".")[0] in sys.stdlib_module_names:
            continue
        if name.startswith(OURS):
            continue
        # The reader, and the engine under it, are asked for by one module,
        # inside a function, so that choosing a provider never loads them.
        assert name in WHEN_ASKED.get(module.name, ()) and not at_the_top, (module.name, name)


def test_loading_the_package_loads_no_providers_library_and_not_the_engine():
    code = (
        "import sys\n"
        "import burro_api.providers.choose, burro_api.providers.measure\n"
        "loaded = {name.split('.')[0] for name in sys.modules}\n"
        "unwanted = {'anthropic', 'openai', 'google', 'httpx', 'httpx2', 'requests', 'urllib3',\n"
        "            'burro_core', 'burro_pipeline', 'pydantic', 'fastapi'}\n"
        "sys.exit(', '.join(sorted(loaded & unwanted)) or 0)\n"
    )

    done = subprocess.run(  # noqa: S603
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=60, check=False
    )

    assert (done.returncode, done.stderr) == (0, "")


def test_nothing_is_printed_and_nothing_is_logged_but_through_the_list():
    for module in MODULES:
        tree = ast.parse(module.read_text(encoding="utf-8"))
        called = [ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)]
        imported = [name for name, _ in imports_of(module)]

        assert "print" not in called, module.name
        assert "logging" not in imported and "warnings" not in imported, module.name
        assert "traceback" not in imported, module.name
        # A failure's words can repeat what was sent. Nothing ever asks for them.
        assert not [call for call in called if call in ("str", "repr", "format")], module.name
        if module.name != "choose.py":
            assert "burro_api.logs" not in imported, module.name


def test_the_only_line_that_is_logged_is_the_one_that_says_a_provider_is_not_used():
    tree = ast.parse((SOURCE / "choose.py").read_text(encoding="utf-8"))
    written = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and ast.unparse(node.func).startswith("logs.")
    ]

    [line] = written
    assert ast.unparse(line.func) == "logs.warning"
    # The name of the event, the provider and the reason, and no field beside them.
    assert len(line.args) == 1 and ast.unparse(line.args[0]) == "NOT_USED"
    assert {keyword.arg for keyword in line.keywords} <= {"provider", "reason", None}
    # Each is the word of an enum of ours, so nothing that was set can stand in it.
    source = (SOURCE / "choose.py").read_text(encoding="utf-8")
    assert "def _warn(provider: Provider | None, refusal: Refusal) -> None:" in source


def test_no_address_is_built_from_a_setting():
    # The host of each provider is a word in its module, and appears once.
    hosts = {
        "gemini.py": "generativelanguage.googleapis.com",
        "openai.py": "api.openai.com",
        "deepseek.py": "api.deepseek.com",
        "anthropic.py": "api.anthropic.com",
    }
    for name, host in hosts.items():
        source = (SOURCE / name).read_text(encoding="utf-8")

        assert f'HOST = "{host}"' in source
        assert "environ" not in source and "getenv" not in source
    for module in MODULES:
        source = module.read_text(encoding="utf-8")
        assert "http://" not in source, module.name
        assert "verify_mode" not in source and "CERT_NONE" not in source, module.name
        assert "check_hostname" not in source, module.name
        assert "_create_unverified_context" not in source, module.name


def test_the_service_still_holds_no_key_of_its_own_making():
    # As the API's own tests ask of every module under it (ADR 0011).
    for module in MODULES:
        source = module.read_text(encoding="utf-8")

        assert "hmac" not in source and "spec_mac" not in source, module.name
        assert "hashlib" not in source, module.name
    assert "keyed" not in {module.stem for module in MODULES}
