# Usage

## CLI

The package installs a `dawgtools` command.

Build a list of available actions:

```bash
uvx --from https://github.com/nhoffman/dawgtools.git dawgtools --help
```

Get detailed help for a specific action:

```bash
uvx --from https://github.com/nhoffman/dawgtools.git dawgtools help <action>
```

## Building the docs locally

From the repository root:

```bash
uv run --with-editable ".[docs]" sphinx-build -b html docs/source docs/_build/html
```

