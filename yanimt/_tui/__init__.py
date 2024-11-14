from typing import Any, ClassVar

from rich.console import Console
from textual.app import App, ComposeResult
from textual.binding import BindingType
from textual.widgets import Footer, Header, TabbedContent

from yanimt._config import AppConfig
from yanimt._database.manager import DatabaseManager
from yanimt._tui.computers import ComputerTable
from yanimt._tui.users import UserTable
from yanimt._util.consts import TCSS_PATH
from yanimt._util.logger import get_null_logger
from yanimt._util.types import Display


class YanimtTui(App[Any]):
    """TUI class of Yanimt."""

    BINDINGS: ClassVar[list[BindingType]] = [("q", "quit", "Quit")]
    CSS_PATH = TCSS_PATH / "object_screen.tcss"

    def __init__(self, config: AppConfig, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        super().__init__(*args, **kwargs)
        self.__config = config

        null_logger = get_null_logger()
        null_console = Console(quiet=True)
        self.__display = Display(null_logger, null_console, False, null_console, False)

        self.__database = DatabaseManager(self.__display, self.__config.db_uri)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(id="header")
        yield Footer(id="footer")
        with TabbedContent("Users", "Computers", id="tabs"):
            yield UserTable(self.__database, id="user_table")
            yield ComputerTable(self.__database, id="computer_table")

    def on_mount(self) -> None:
        """Set up tabs."""
        self.get_widget_by_id("user_table").focus()

    async def action_quit(self) -> None:
        self.app.exit()
