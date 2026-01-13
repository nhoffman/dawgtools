# dawgtools

See https://nhoffman.github.io/dawgtools/ for full documentation

## installation and use

The database features of this package are intended to be used in the
`am-dawg-tool` environment, but other features can be used from anywhere
uv can be installed.

Some setup is required before the first use.

The commands below are intended to be run from within a bash shell. VS
Code is the recommended terminal environment in `am-dawg-tool`:

https://code.visualstudio.com/docs/terminal/basics

In `am-dawg-tool`, the terminal opens with a powershell prompt. First,
start a bash shell:

```
bash
```

### uv

We will use uv to manage python versions and dependencies. The
instructions in this section only need to be completed once. The first
step is to install uv.

See https://docs.astral.sh/uv/getting-started/installation/ for
details on uv installation.

The following commands install ``uv`` and ``uvx`` to
``$HOME/.local/bin``. They also modify your bash profile
(``~/.bashrc``) to add this directory to your PATH the next time you
start a shell.

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

The uv installer fails to update `$HOME/.bashrc` for some users; let's
make sure this is done.

```
curl -LsSf https://raw.githubusercontent.com/nhoffman/dawgtools/refs/heads/main/update-bashrc.bash | bash
```

The following command allows you to start using uv immediately;
alternatively, you can exit and start a new bash shell.

```
source "$HOME/.local/bin/env"
```

Once uv is installed, install a recent version of python:

```
uv python install 3.13
```

Confirm which python versions are available:

```
uv python list
```

Run the uv-managed version of python (uv will choose the most recent
version by default):

```
$ uv run python --version
```

See the uv docs for additional options.

### dawgtools

Most users should execute commands using uvx from the github
repository. This executes the most recent version of the package with
all of the necessary dependencies added on the fly. This will take a
few seconds the first time; it's faster on subsequent runs.

```
uvx --from https://github.com/nhoffman/dawgtools.git dawgtools --help
```

To execute a subcommand, simply include extra arguments:

```
uvx --from https://github.com/nhoffman/dawgtools.git dawgtools sql2csv -q 'select 1 as col1, 2 as col2'
```

This should produce the following output:

```
col1,col2
1,2
```

For development, run a command from within a cloned version of the
repository:

```
uv run --with-editable . dawgtools --help
```

Or with a specific python version:

```
uv run --python 3.12 --with . dawgtools --help
```

On MacOS (for development of capabilities unrelated to database
access), you may need to install `unixodbc`:

```
brew install unixodbc
```


Run tests:

```
uv run --with-editable . --with pytest pytest
```

## documentation

Build HTML documentation with Sphinx:

```
uv run --with-editable ".[docs]" sphinx-build -b html docs/source docs/_build/html
```

To publish documentation with GitHub Pages, enable Pages for this repo (Settings → Pages → Source: GitHub Actions). The workflow is in `.github/workflows/docs.yml`.
