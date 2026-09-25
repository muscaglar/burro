"""The command line of the desk: what each command refuses, and what it says.

Every name and id here is made up. No socket is opened: the command that serves is
tested through its own port in `test_server.py`.
"""

import importlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from desk import cli, records, server


def test_the_made_up_city_is_filled_only_into_a_folder_named_for_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    # `data/raw/desk` is where a build of London looks. The made-up city never goes there.
    for folder in (tmp_path / "desk", tmp_path / "desk-synthetic-old", tmp_path / "synthetic"):
        assert cli.main(["fill", "--made-up", "--data", str(folder)]) == cli.REFUSED
        assert not folder.exists()
        said = capsys.readouterr()
        assert said.out == ""
        assert said.err == (
            "Not filled. The made-up city is filled only into a folder whose name ends "
            "-synthetic, such as data/raw/desk-synthetic.\n"
        )


def test_the_made_up_city_is_filled_into_a_folder_named_for_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    folder = tmp_path / "walk-synthetic"
    assert cli.main(["fill", "--made-up", "--data", str(folder)]) == cli.OK
    assert (folder / "items" / "names.jsonl").is_file()
    assert capsys.readouterr().out.startswith("Filled from the made-up city.")


def test_the_folder_the_desk_fills_by_itself_is_named_for_the_made_up_city():
    assert cli.MADE_UP.name.endswith(cli.NAMED_MADE_UP)
    assert not cli.REAL.name.endswith(cli.NAMED_MADE_UP)


def answer(data: Path, queue: str, at: int, code: str, **more: object) -> None:
    """One answer to an item of the made-up city, as the server writes it."""
    rows = (data / "items" / f"{queue}.jsonl").read_text(encoding="utf-8").splitlines()
    item = json.loads(rows[at + 1])
    records.append(
        records.path_of(data, queue, "r1"),
        reviewer="r1",
        queue=queue,
        question=f"{queue}@1",
        item=item["id"],
        rev=item["rev"],
        answer=code,
        detail=item["preset"],
        synthetic=True,
        clock=lambda: datetime(2026, 10, 6, 21, 14, 9, tzinfo=UTC),
        **more,  # type: ignore[arg-type]
    )


def test_compile_says_how_many_answers_were_flagged_and_where_they_are_listed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)
    data = tmp_path / "walk-synthetic"
    assert cli.main(["fill", "--made-up", "--data", str(data)]) == cli.OK
    answer(data, "borders", 0, "right")
    answer(data, "borders", 1, "wrong", note="A made-up reason.")
    answer(data, "borders", 2, "unknown")
    answer(data, "kinds", 0, "yes", second=True)
    answer(data, "kinds", 1, "skip", note="A made-up note.")
    capsys.readouterr()
    assert cli.main(["compile", "--data", str(data)]) == cli.OK
    said = capsys.readouterr().out.splitlines()
    assert said[1].split() == ["queue", "applied", "not", "applied", "flagged"]
    table = {row.split()[0]: row.split()[1:] for row in said[2:] if row[:1].islower()}
    assert table["borders"] == ["1", "0", "2"]
    assert table["kinds"] == ["1", "0", "0"]
    assert (
        "To look at: 1 called wrong, 1 not known, 1 marked for a second reviewer, "
        "1 skipped with a note or a mark." in said
    )
    listed = "walk-synthetic/out/private/to_look_at.csv"
    assert f"They are listed in {listed}, each with its note." in said


def test_compile_says_that_a_name_turned_down_waits_for_the_draft_to_be_made_again(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)
    data = tmp_path / "walk-synthetic"
    assert cli.main(["fill", "--made-up", "--data", str(data)]) == cli.OK
    answer(data, "names", 0, "drop")
    answer(data, "names", 1, "area")
    capsys.readouterr()
    assert cli.main(["compile", "--data", str(data)]) == cli.OK
    said = capsys.readouterr().out
    assert (
        "1 name was turned down while its area has ground. It is set aside until the "
        "draft is made again.\n" in said
    )
    assert (
        "Make the draft again from walk-synthetic/out/names.csv, fill the queues again, "
        "and only then look at borders.\n" in said
    )


def test_compile_says_nothing_of_a_new_draft_when_no_name_waits_for_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    data = tmp_path / "walk-synthetic"
    assert cli.main(["fill", "--made-up", "--data", str(data)]) == cli.OK
    answer(data, "names", 0, "area")
    capsys.readouterr()
    assert cli.main(["compile", "--data", str(data)]) == cli.OK
    assert "draft is made again" not in capsys.readouterr().out


def test_compile_says_so_when_nothing_was_flagged(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    data = tmp_path / "walk-synthetic"
    assert cli.main(["fill", "--made-up", "--data", str(data)]) == cli.OK
    answer(data, "borders", 0, "right")
    capsys.readouterr()
    assert cli.main(["compile", "--data", str(data)]) == cli.OK
    assert "To look at: nothing." in capsys.readouterr().out.splitlines()


# The second copy of every decision, and where it is kept


class Started:
    """Stands in for the server once it is bound, so that no socket is opened."""

    server_address = ("127.0.0.1", 8765)

    def serve_forever(self) -> None:
        raise KeyboardInterrupt

    def server_close(self) -> None:
        """Nothing was opened."""


@pytest.fixture
def at_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A home folder of the test's own, and a desk that binds no port."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    def bind_no_port(desk: object, port: int) -> Started:
        return Started()

    monkeypatch.setattr(cli.server, "serve", bind_no_port)
    return home


def london(tmp_path: Path) -> Path:
    """A folder of items that say they are real. They are the made-up city's."""
    made_up = tmp_path / "walk-synthetic"
    assert cli.main(["fill", "--made-up", "--data", str(made_up)]) == cli.OK
    data = tmp_path / "desk"
    (data / "items").mkdir(parents=True)
    rows = (made_up / "items" / "kinds.jsonl").read_text(encoding="utf-8").splitlines()
    first = json.loads(rows[0]) | {"synthetic": False}
    text = "\n".join([json.dumps(first), *rows[1:]]) + "\n"
    (data / "items" / "kinds.jsonl").write_text(text, encoding="utf-8")
    return data


def test_real_data_is_served_with_its_second_copy_in_a_folder_of_the_home_folder(
    tmp_path: Path, at_home: Path, capsys: pytest.CaptureFixture[str]
):
    """The founder decided where the second copy is kept. No KEEP is given, and the desk
    finds the folder by its name in the home folder of whoever starts it."""
    data = london(tmp_path)
    (at_home / cli.KEPT_IN_HOME).mkdir()
    capsys.readouterr()
    assert cli.serve("r1", 8765, data, None) == cli.OK
    said = capsys.readouterr().out
    assert "REAL DATA FOR LONDON" in said
    assert f"A second copy of every decision is kept in {at_home / cli.KEPT_IN_HOME}." in said


def test_real_data_is_not_served_where_the_home_folder_holds_no_such_folder(
    tmp_path: Path, at_home: Path, capsys: pytest.CaptureFixture[str]
):
    """The desk makes no folder by itself: a folder it made could be taken for the copy
    of an earlier sitting, and would hold nothing of it."""
    data = london(tmp_path)
    capsys.readouterr()
    assert cli.serve("r1", 8765, data, None) == cli.REFUSED
    said = capsys.readouterr()
    assert said.out == ""
    assert said.err == (
        "The desk did not start. On real data the desk keeps a second copy of every "
        "decision, outside the repository, because one git command can remove the first. "
        "Make the folder burro-desk-decisions in your home folder, or name another: "
        "make desk KEEP=FOLDER.\n"
    )
    assert list(at_home.iterdir()) == []


def test_a_folder_that_is_named_is_where_the_copy_is_kept_whatever_the_home_folder_holds(
    tmp_path: Path, at_home: Path, capsys: pytest.CaptureFixture[str]
):
    data = london(tmp_path)
    (at_home / cli.KEPT_IN_HOME).mkdir()
    named = tmp_path / "kept-elsewhere"
    assert cli.serve("r1", 8765, data, named) == cli.OK
    assert f"is kept in {named}." in capsys.readouterr().out
    assert list((at_home / cli.KEPT_IN_HOME).iterdir()) == []


def test_the_made_up_city_keeps_no_copy_though_the_folder_is_there(
    tmp_path: Path, at_home: Path, capsys: pytest.CaptureFixture[str]
):
    (at_home / cli.KEPT_IN_HOME).mkdir()
    made_up = tmp_path / "walk-synthetic"
    assert cli.main(["fill", "--made-up", "--data", str(made_up)]) == cli.OK
    capsys.readouterr()
    assert cli.serve("r1", 8765, made_up, None) == cli.OK
    assert "second copy" not in capsys.readouterr().out
    assert list((at_home / cli.KEPT_IN_HOME).iterdir()) == []


def test_a_file_in_the_place_of_the_folder_is_no_folder_for_the_copy(
    tmp_path: Path, at_home: Path, capsys: pytest.CaptureFixture[str]
):
    data = london(tmp_path)
    (at_home / cli.KEPT_IN_HOME).write_text("not a folder", encoding="utf-8")
    assert cli.serve("r1", 8765, data, None) == cli.REFUSED
    assert "Make the folder burro-desk-decisions" in capsys.readouterr().err


def test_the_folder_is_named_in_the_guide_and_the_code_holds_no_path_of_any_machine():
    """The code holds the name of the folder and asks where the home folder is. It holds
    no path: a path names a machine, and whoever works on it."""
    assert cli.KEPT_IN_HOME == "burro-desk-decisions"
    guide = (cli.ROOT / "docs" / "design" / "desk.md").read_text(encoding="utf-8")
    assert f"`~/{cli.KEPT_IN_HOME}`" in guide
    assert f"mkdir ~/{cli.KEPT_IN_HOME}" in guide
    for path in sorted(cli.HERE.rglob("*.py")):
        if "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"""["'](~|/Users/|/home/|[A-Z]:\\)""", text), path.name


# The panel


def test_the_made_up_city_is_shown_the_committed_release_where_none_is_named(tmp_path: Path):
    panel, said = cli.panel_for(None, tmp_path / "desk-synthetic")
    assert panel is not None and panel.synthetic is True
    assert said.startswith("The panel shows the release in ")
    assert said.endswith("syn-2026-09-23-01.")


def test_real_data_is_shown_no_release_unless_one_is_named(tmp_path: Path):
    # Nothing made up is ever shown beside real data because nothing else was named.
    assert cli.panel_for(None, tmp_path / "desk") == (None, cli.NO_RELEASE)
    assert "make desk RELEASE=FOLDER" in cli.NO_RELEASE


def test_the_queues_are_served_where_the_packages_of_the_panel_are_not_installed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    def missing(name: str) -> Any:
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(importlib, "import_module", missing)
    assert cli.panel_for(None, tmp_path / "desk-synthetic") == (None, cli.NO_PACKAGES)
    assert "make setup" in cli.NO_PACKAGES


def test_a_folder_that_is_no_release_is_refused_in_words(tmp_path: Path):
    with pytest.raises(records.Unfit, match=r"The release cannot be shown\. .*manifest\.json"):
        cli.panel_for(tmp_path, tmp_path / "desk-synthetic")


def test_the_made_up_city_and_london_are_never_shown_together(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    data = tmp_path / "walk-synthetic"
    assert cli.main(["fill", "--made-up", "--data", str(data)]) == cli.OK

    def open_panel(release: Path) -> Any:
        return SimpleNamespace(synthetic=False)

    def found(name: str) -> Any:
        return SimpleNamespace(open_panel=open_panel)

    monkeypatch.setattr(importlib, "import_module", found)
    capsys.readouterr()
    # It is refused before any port is opened.
    assert cli.serve("r1", 0, data, release=tmp_path) == cli.REFUSED
    assert capsys.readouterr().err == f"The desk did not start. {cli.OTHER_CITY}.\n"


# A release, and no queue


def a_panel_of_london(monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    """Stand in for the panel of a release that is not made up. It says what it was shown."""
    shown: list[Path] = []

    class Panel:
        synthetic = False

        def answer(self, desk: Any, what: str, of: str | None, sent: object) -> dict[str, Any]:
            return {"waiting": [], "what": what}

    def open_panel(release: Path) -> Any:
        shown.append(release)
        return Panel()

    def found(name: str) -> Any:
        return SimpleNamespace(open_panel=open_panel)

    monkeypatch.setattr(importlib, "import_module", found)
    return shown


def test_with_a_release_and_no_queue_filled_the_desk_keeps_what_is_decided_where_london_is_kept(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(cli, "REAL", tmp_path / "raw" / "desk")
    monkeypatch.setattr(cli, "MADE_UP", tmp_path / "raw" / "desk-synthetic")
    assert cli.folder_for(None, None) == cli.MADE_UP
    assert cli.folder_for(None, tmp_path / "releases" / "syn-2026-09-23-01") == cli.MADE_UP
    # A release of London is never shown beside the made-up city because no folder was named.
    assert cli.folder_for(None, tmp_path / "releases" / "lon-2026-09-25-01") == cli.REAL
    assert cli.folder_for(tmp_path / "mine", tmp_path / "lon-2026-09-25-01") == tmp_path / "mine"
    (cli.REAL / "items").mkdir(parents=True)
    assert cli.folder_for(None, None) == cli.REAL


def test_the_panel_opens_on_a_release_where_no_queue_is_filled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    shown = a_panel_of_london(monkeypatch)
    release, data, keep = tmp_path / "lon-2026-09-25-01", tmp_path / "desk", tmp_path / "keep"
    keep.mkdir()
    panel, said = cli.panel_for(release, data)
    assert shown == [release] and said.startswith("The panel shows the release in ")
    desk = server.open_desk(data, cli.PAGE, cli.QUESTIONS, "r1", keep=keep, panel=panel)
    assert (desk.synthetic, dict(desk.items)) == (False, {})
    found = server.state(desk)
    assert (found["queues"], found["resume"]) == ([], None)
    assert found["banner"] == server.BANNER[False]
    assert server.first_page(desk) == server.PANEL_PAGE


def test_with_no_release_and_no_queue_there_is_nothing_to_show(tmp_path: Path):
    with pytest.raises(records.Unfit, match="There is no item to show"):
        server.open_desk(tmp_path / "desk", cli.PAGE, cli.QUESTIONS, "r1", keep=tmp_path)


def test_real_data_with_no_queue_still_needs_its_second_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    a_panel_of_london(monkeypatch)
    panel, _ = cli.panel_for(tmp_path / "lon-2026-09-25-01", tmp_path / "desk")
    with pytest.raises(server.NeedsKeep):
        server.open_desk(tmp_path / "desk", cli.PAGE, cli.QUESTIONS, "r1", panel=panel)


def test_a_release_alone_is_started_and_says_that_no_queue_is_filled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    a_panel_of_london(monkeypatch)
    monkeypatch.setattr(cli, "REAL", tmp_path / "raw" / "desk")
    monkeypatch.setattr(cli, "MADE_UP", tmp_path / "raw" / "desk-synthetic")
    keep = tmp_path / "keep"
    keep.mkdir()

    class Stopped:
        server_address = ("127.0.0.1", 8765)

        def serve_forever(self) -> None:
            raise KeyboardInterrupt

        def server_close(self) -> None:
            return None

    def started(desk: server.Desk, port: int) -> Any:
        return Stopped()

    monkeypatch.setattr(server, "serve", started)
    assert cli.serve("r1", 0, None, keep, tmp_path / "lon-2026-09-25-01") == cli.OK
    said = capsys.readouterr().out.splitlines()
    assert said[1] == server.BANNER[False]
    assert cli.NO_QUEUE in said
    assert not cli.MADE_UP.exists(), "the made-up city is not filled beside London"
