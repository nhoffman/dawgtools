# Usage

## CLI

The package installs a `dawgtools` command.

Build a list of available actions:

```bash
uvx --from "git+https://github.com/nhoffman/dawgtools.git@main" dawgtools --help
```

To run a branch, append its name after `@` in the Git URL:

```bash
uvx --from "git+https://github.com/nhoffman/dawgtools.git@pinned-deps" dawgtools --help
```

Get detailed help for a specific action:

```bash
uvx --from "git+https://github.com/nhoffman/dawgtools.git@main" dawgtools help <action>
```

## Building the docs locally

From the repository root:

```bash
uv run --with-editable ".[docs]" sphinx-build -b html docs/source docs/_build/html
```
