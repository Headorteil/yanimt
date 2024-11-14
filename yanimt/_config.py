"""Config module for Yanimt."""

from logging import Logger
from pathlib import Path

from yaml import safe_load

from yanimt._util.consts import DEFAULT_DB_URI, DEFAULT_TOOL_DIR


class AppConfig:
    """Config class for Yanimt."""

    def __init__(self, logger: Logger, config_path: Path) -> None:
        """Initialize the AppConfig class."""
        self.__config_path = config_path
        self.__logger = logger

        self.db_uri = DEFAULT_DB_URI

    def init_dir(self) -> None:
        """Create default config directory if it doesn't exist."""
        if (
            self.__config_path.parent == DEFAULT_TOOL_DIR
            and not DEFAULT_TOOL_DIR.is_dir()
        ):
            self.__logger.info("First use, creating tool dir -> %s", DEFAULT_TOOL_DIR)
            DEFAULT_TOOL_DIR.mkdir()

    def init_config(self) -> None:
        """Return the config."""
        self.init_dir()

        if self.__config_path.is_file():
            raw_config = safe_load(self.__config_path.read_text())

            if raw_config.get("db_uri"):
                self.db_uri = raw_config["db_uri"]

        self.__logger.debug("Loaded config -> db_uri : %s", self.db_uri)
