"""Cli module for Yanimt."""

import importlib.metadata
from pathlib import Path
from types import SimpleNamespace
from typing import Annotated

import typer
from rich.console import Console

from yanimt._config import AppConfig
from yanimt._tui import YanimtTui
from yanimt._util.consts import DEFAULT_CONFIG_FILE
from yanimt._util.exceptions import HandledError
from yanimt._util.logger import add_file_handler, get_logger
from yanimt.cli.gather import app as gather_app

app = typer.Typer(
    pretty_exceptions_enable=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Yanimt by Headorteil 😎",
    epilog="""Examples :\n\n\n
- Get tool version\n
yanimt -V\n
- Access the terminal user interface\n
yanimt\n
- Gather all infos from the domain\n
yanimt gather -u <username> -p <password> -i <dc ip> all""",
)
app.add_typer(gather_app, name="gather")


def __version_callback(value: bool) -> None:
    if value:
        version = importlib.metadata.version("yanimt")
        print(version)  # noqa: T201
        raise typer.Exit


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[  # noqa: ARG001
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=__version_callback,
            is_eager=True,
            help="Print the tool version",
        ),
    ] = False,
    config_path: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            file_okay=True,
            readable=True,
            resolve_path=True,
            help="Config path",
        ),
    ] = DEFAULT_CONFIG_FILE,
    verbosity: Annotated[
        int,
        typer.Option(
            "--verbosity-level", "-v", min=0, max=3, help="Change the logs verbosity"
        ),
    ] = 2,
    display: Annotated[
        bool,
        typer.Option(
            "--display/--no-display",
            " /-D",
            help="Display things that are not logs nor live like tables",
        ),
    ] = True,
    pager: Annotated[
        bool,
        typer.Option(
            "--pager/--no-pager",
            "-p/-P",
            help="Display things that are not logs nor live like tables in less",
        ),
    ] = False,
    live: Annotated[
        bool,
        typer.Option(
            "--live/--no-live", "-l/-L", help="Display live objects like progress bars"
        ),
    ] = True,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug", "-d", help="Use max verbosity and print file infos with logs"
        ),
    ] = False,
) -> None:
    """Set variables for all subcommands and run TUI if no command is provided."""
    console = Console()

    if debug:
        verbosity = 3

    logger = get_logger(console, verbosity, debug)

    try:
        config = AppConfig(logger, config_path)
        config.init_config()
    except HandledError as e:
        logger.critical(e)
        raise typer.Exit(code=1) from e
    except Exception as e:
        logger.critical("Can't parse config file -> %s", e)
        raise typer.Exit(code=1) from e

    add_file_handler(logger, config.log_file)

    if ctx.invoked_subcommand is None:
        tui = YanimtTui(config)
        tui.run()
        raise typer.Exit

    if debug:
        no_stacktrace_exceptions = ()
        stacktrace_exceptions = BaseException
    else:
        no_stacktrace_exceptions = HandledError
        stacktrace_exceptions = Exception

    ctx.obj = SimpleNamespace(
        console=console,
        display=display,
        logger=logger,
        pager=pager,
        live=live,
        debug=debug,
        config=config,
        no_stacktrace_exceptions=no_stacktrace_exceptions,
        stacktrace_exceptions=stacktrace_exceptions,
    )


@app.command("clear-db", help="Clear the database")
def clear_db(ctx: typer.Context) -> None:
    db_file = Path(ctx.obj.config.db_uri.replace("sqlite:///", ""))
    if db_file.is_file():
        db_file.unlink()
        ctx.obj.logger.info("Database was droped")
    else:
        ctx.obj.logger.info("Database doesn't exist")
