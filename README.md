# dawgtools

## installation and use

The commands below are intended to be run from within a bash shell. VS
Code is the recommended terminal environment:

https://code.visualstudio.com/docs/terminal/basics

At the powershell prompt, start a bash shell:

```
bash
```

### uv

This package is intended to be run using uv in the am-dawg-tool
environment. The first step is to install uv.

See https://docs.astral.sh/uv/getting-started/installation/

```
curl -LsSf https://astral.sh/uv/install.sh | sh
exit # quit this shell and start a new one after installing
```

The command above installs ``uv`` and ``uvx`` commands to
``$HOME/.local/bin``. It also modifies ``~/.bashrc`` to add this
directory to your PATH the next time you start a shell.

Once uv is installed, install a recent version of python:

```
uv python install 3.12
```

Confirm which python versions are available:

```
uv python list
```

Run the uv-managed version of python (uv will choose the most recent version by default):

```
$ uv run python --version
Python 3.12.8
$ uv run --python 3.9 python --version
Python 3.9.18
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

For development, run a command from within a cloned version of the
repository:

```
uv run --with . dawgtools --help
```

Or with a specific python version:

```
uv run --python 3.12 --with . dawgtools --help
```

