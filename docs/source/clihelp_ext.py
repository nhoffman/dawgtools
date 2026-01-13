from __future__ import annotations

import io
import os
import pkgutil
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CliHelpResult:
    subcommand: str
    help_text: str
    error: str | None = None


def _list_subcommands() -> list[str]:
    import dawgtools.commands

    modules = [name for _, name, _ in pkgutil.iter_modules(dawgtools.commands.__path__)]
    return sorted(m for m in modules if not m.startswith("_"))


def _capture_help(subcommand: str) -> CliHelpResult:
    import logging

    logging.getLogger("dawgtools").setLevel(logging.ERROR)
    logging.getLogger("dawgtools.db").setLevel(logging.ERROR)

    from dawgtools.main import parse_arguments

    buf = io.StringIO()
    old_argv0 = sys.argv[0]
    try:
        sys.argv[0] = "dawgtools"
        with redirect_stdout(buf):
            try:
                parse_arguments([subcommand, "-h"])
            except SystemExit:
                pass
    except Exception as exc:  # keep docs builds resilient
        return CliHelpResult(subcommand=subcommand, help_text=buf.getvalue(), error=str(exc))
    finally:
        sys.argv[0] = old_argv0

    return CliHelpResult(subcommand=subcommand, help_text=buf.getvalue())


def _render_markdown(results: list[CliHelpResult]) -> str:
    lines: list[str] = []
    lines.append("# CLI help")
    lines.append("")
    lines.append("This page is generated from `dawgtools <subcommand> -h` output during the Sphinx build.")
    lines.append("")

    for result in results:
        lines.append(f"## `dawgtools {result.subcommand} -h`")
        lines.append("")
        if result.error:
            lines.append(f"Build-time error capturing help: `{result.error}`")
            lines.append("")
        lines.append("```text")
        lines.append(result.help_text.rstrip("\n"))
        lines.append("```")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _generate_cli_help_pages(app) -> None:
    if os.environ.get("DAWGTOOLS_DOCS_SKIP_CLIHELP") == "1":
        return

    source_dir = Path(app.confdir)
    out_path = source_dir / "cli_generated.md"

    results = [_capture_help(cmd) for cmd in _list_subcommands()]
    out_path.write_text(_render_markdown(results), encoding="utf-8")


def setup(app):
    app.connect("builder-inited", _generate_cli_help_pages)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
