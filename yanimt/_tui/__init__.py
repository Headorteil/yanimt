from collections.abc import Iterable
from typing import Any, ClassVar

from rich.console import Console
from textual import work
from textual.app import App, ComposeResult, SystemCommand
from textual.binding import BindingType
from textual.screen import Screen
from textual.widgets import Footer, Header, RichLog, TabbedContent

from yanimt._config import AppConfig
from yanimt._database.manager import DatabaseManager
from yanimt._tui.computers import ComputerTable
from yanimt._tui.gather import InitGatherScreen
from yanimt._tui.logger import get_tui_logger
from yanimt._tui.users import UserTable
from yanimt._util.consts import TCSS_PATH
from yanimt._util.logger import get_null_logger
from yanimt._util.types import Display
from yanimt.gatherer import YanimtGatherer


class YanimtTui(App[Any]):
    """TUI class of Yanimt."""

    BINDINGS: ClassVar[list[BindingType]] = [("q", "quit", "Quit")]
    CSS_PATH = TCSS_PATH / "object_screen.tcss"

    def __init__(self, config: AppConfig, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        super().__init__(*args, **kwargs)
        self.config = config

        null_logger = get_null_logger()
        null_console = Console(quiet=True)
        self.display_ = Display(null_logger, null_console, False, null_console, False)

        self.database = DatabaseManager(self.display_, self.config.db_uri)
        self.gatherer = None
        self.logger = None

    def get_system_commands(self, screen: Screen[Any]) -> Iterable[SystemCommand]:
        yield from super().get_system_commands(screen)
        yield SystemCommand(
            "Gather init", "Initialize the gather module", self.init_gather_command
        )
        yield SystemCommand(
            "Gather all", "Gather all datas from AD", self.gather_command
        )

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(id="header")
        yield Footer(id="footer")
        with TabbedContent("Users", "Computers", "Logs", id="tabs"):
            yield UserTable(id="user_table")
            yield ComputerTable(id="computer_table")
            yield RichLog(id="logs_table")

    def on_mount(self) -> None:
        """Set up tabs."""
        self.logger = get_tui_logger(self.get_widget_by_id("logs_table"))  # pyright: ignore [reportArgumentType]
        self.get_widget_by_id("user_table").focus()

    async def action_quit(self) -> None:
        self.exit()

    def init_gather_command(self) -> None:
        self.push_screen(InitGatherScreen())

    @work
    async def gather_command(self) -> None:
        if self.gatherer is None:
            config = self.config  # pyright: ignore [reportAttributeAccessIssue]
            try:
                self.gatherer = YanimtGatherer(
                    config,
                    logger=self.logger,  # pyright: ignore [reportAttributeAccessIssue]
                    live=False,
                    username=config.username,
                    password=config.password,
                    hashes=config.hashes,
                    auth_proto=config.auth_proto,
                    aes_key=config.aes_key,
                    ccache_path=config.ccache_path,
                    domain=config.domain,
                    dc_ip=config.dc_ip,
                    dc_host=config.dc_host,
                    ldap_scheme=config.ldap_scheme,
                    dns_ip=config.dns_ip,
                    dns_proto=config.dns_proto,
                )
            except Exception:
                self.logger.exception("Unhandled exception")  # pyright: ignore [reportOptionalMemberAccess]
                await self.push_screen_wait(InitGatherScreen())

        self.gather_all()

    @work(exclusive=True, thread=True)
    def gather_all(self) -> None:
        try:
            self.get_widget_by_id("logs_table").focus()
            self.gatherer.all_()  # pyright: ignore [reportOptionalMemberAccess]
        except Exception as e:
            self.logger.exception("Unhandled exception")  # pyright: ignore [reportOptionalMemberAccess]
            self.notify(str(e), title="Error", severity="error")
        else:
            self.notify(
                "All datas successfully gathered",
                title="Success",
                severity="information",
            )
