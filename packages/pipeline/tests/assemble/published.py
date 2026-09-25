"""A file of changes as a build takes it: published, and committed to a repository.

A build reads a file of changes only as the repository holds it, at the commit that is
checked out. So a test that builds from one makes a repository of its own, with git itself,
and commits the file there. Every line and every reason is made up.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..evidence.support import GIT, git

# Where `desk publish` puts the founder's file, under the folder it is handed.
PUBLISHED_AT = Path("gazetteer") / "quillhaven" / "decisions" / "changes"
NO_GIT = "git is needed to make a repository that holds the file of changes"


@dataclass(frozen=True)
class Published:
    """A file of changes in a repository of a test, and what a build is told of it."""

    root: Path
    path: Path
    commit: str

    def arguments(self) -> tuple[str, ...]:
        """What the build is handed: the file, the repository it is in, and its commit."""
        return ("--changes", str(self.path), "--root", str(self.root), "--commit", self.commit)


def written(lines: tuple[dict[str, Any], ...] | bytes) -> bytes:
    if isinstance(lines, bytes):
        return lines
    return "".join(json.dumps(line) + "\n" for line in lines).encode()


def published(
    folder: Path, *lines: dict[str, Any], name: str = "r1.jsonl", content: bytes | None = None
) -> Published:
    """A repository in `folder` that holds the file, committed, and nothing else that matters."""
    assert GIT is not None, NO_GIT
    root = folder / "repository"
    path = root / PUBLISHED_AT / name
    path.parent.mkdir(parents=True)
    path.write_bytes(written(lines) if content is None else content)
    (root / "README.md").write_text("A made-up repository.\n", encoding="utf-8")
    git(root, "init", "--quiet", "--initial-branch", "main")
    git(root, "add", "--all")
    git(root, "commit", "--quiet", "--message", "Publish what was decided")
    return Published(root, path, git(root, "rev-parse", "HEAD"))
