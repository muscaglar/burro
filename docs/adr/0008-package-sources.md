# 0008. Where packages come from

Status: accepted, 2026-09-23. The lockfile steps below are still to do.

## Context

The repository is hosted on GitHub, and hosted CI installs from the public index.

1. A lockfile records the address of every package. One made with package settings other than the public index names an address that nobody else could install from, so only a lockfile made from the public index is committed.
2. A contributor's machine decides where packages come from and what may be installed on it. The project works within that and never overrides it.
3. The project's tools must run the same way on any contributor's machine and in CI, so it does not depend on an executable that arrives inside a package.

## Decision

**Now, until the lockfiles are committed**

- The project does not pin a package index. `uv` uses whatever the machine is configured for.
- `uv.lock` is not committed. It is listed in `.gitignore`.
- Hosted CI runs on GitHub's runners and installs from the public index, without a lockfile.
- The project installs no package that ships a native binary it needs to run. Python console scripts and compiled extension modules are fine. `ruff` and `pyright` are prerequisites installed by the system package manager, like `uv` itself. CI installs pinned versions of both.
- `make` is the task runner, because it is already present everywhere.
- `make public-only` fails if a lockfile or a package settings file names any host outside the public allowlist, or if any file contains a URL with credentials. It covers uv, pip, poetry, npm, yarn, pnpm and Swift packages, Dockerfiles and CI workflows, and it fails closed: in those files a URL under any key must be on the allowlist. To use another public host, add it to the allowlist in `tools/check_public_only.py`. As a backstop it also reads the machine's own package settings and fails if any file mentions a host that is private there, in any form. It looks at what git would track and at what is staged. It checks against an allowlist so that no private hostname is ever written here. It is not a secret scanner: add one as a system prerequisite when the first real credential exists.

**Still to do: commit the lockfiles**

1. Pin the public index in `pyproject.toml`.
2. Run `uv lock` and commit `uv.lock`. Remove it from `.gitignore`.
3. Change CI from `uv sync` to `uv sync --locked`.
4. Move `ruff` and `pyright` into the `dev` dependency group, so their versions are locked too.

## Consequences

- Until the lockfiles are committed, two installs can resolve different versions, and CI can break when a dependency publishes a release. Version ranges in `pyproject.toml` are the only pin.
- `ruff` and `pyright` versions can drift between a contributor's machine and CI.
- Work that needs a native tool from a package, such as the routing engine in phase 0b, runs in CI.

## What would change it

Nothing, once the four steps above are done. This record then describes history.
