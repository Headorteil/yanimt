"""Config module for Yanimt."""

from logging import Logger
from pathlib import Path
from typing import Any

from yaml import safe_dump, safe_load

from yanimt._util.consts import (
    DEFAULT_DB_URI,
    DEFAULT_LOG_DIR,
    DEFAULT_LOG_FILE,
    DEFAULT_TOOL_DIR,
)
from yanimt._util.exceptions import HandledError
from yanimt._util.types import AuthProto, DnsProto, LdapScheme


class AppConfig:
    """Config class for Yanimt."""

    def __init__(self, logger: Logger, config_path: Path) -> None:
        """Initialize the AppConfig class."""
        self.config_path = config_path
        self.__logger = logger

        self.db_uri = DEFAULT_DB_URI
        self.log_file = DEFAULT_LOG_FILE
        self.username = None
        self.password = None
        self.domain = None
        self.aes_key = None
        self.ccache_path = None
        self.auth_proto = AuthProto.AUTO
        self.dc_ip = None
        self.dc_host = None
        self.ldap_scheme = LdapScheme.AUTO
        self.dns_ip = None
        self.dns_proto = DnsProto.AUTO
        self.hashes = None

    def init_dir(self) -> None:
        """Create default config directory if it doesn't exist."""
        if (
            self.config_path.parent == DEFAULT_TOOL_DIR
            and not DEFAULT_TOOL_DIR.is_dir()
        ):
            self.__logger.info("First use, creating tool dir -> %s", DEFAULT_TOOL_DIR)
            DEFAULT_TOOL_DIR.mkdir()

    def init_config(self) -> None:
        """Return the config."""
        self.init_dir()

        if self.config_path.is_file():
            raw_config = safe_load(self.config_path.read_text())
            if raw_config is not None:
                if raw_config.get("db_uri"):
                    self.db_uri = raw_config["db_uri"]
                if raw_config.get("log_file"):
                    self.log_file = Path(raw_config["log_file"])
                if raw_config.get("username"):
                    self.username = raw_config["username"]
                if raw_config.get("password"):
                    self.password = raw_config["password"]
                if raw_config.get("hashes"):
                    self.hashes = raw_config["password"]
                if raw_config.get("auth_proto"):
                    try:
                        self.auth_proto = AuthProto(raw_config["auth_proto"])
                    except ValueError as e:
                        errmsg = "Invalid auth proto in config file"
                        raise HandledError(errmsg) from e
                if raw_config.get("aes_key"):
                    self.aes_key = raw_config["aes_key"]
                if raw_config.get("ccache_path"):
                    self.ccache_path = Path(raw_config["ccache_path"])
                if raw_config.get("domain"):
                    self.domain = raw_config["domain"]
                if raw_config.get("dc_ip"):
                    self.dc_ip = raw_config["dc_ip"]
                if raw_config.get("dc_host"):
                    self.dc_host = raw_config["dc_host"]
                if raw_config.get("ldap_scheme"):
                    try:
                        self.ldap_scheme = LdapScheme(raw_config["ldap_scheme"])
                    except ValueError as e:
                        errmsg = "Invalid ldap scheme in config file"
                        raise HandledError(errmsg) from e
                if raw_config.get("dns_ip"):
                    self.dns_ip = raw_config["dns_ip"]
                if raw_config.get("dns_proto"):
                    try:
                        self.dns_proto = DnsProto(raw_config["dns_proto"])
                    except ValueError as e:
                        errmsg = "Invalid dns proto in config file"
                        raise HandledError(errmsg) from e

        if self.log_file.parent == DEFAULT_LOG_DIR and not DEFAULT_LOG_DIR.is_dir():
            self.__logger.info("Creating default logs dir -> %s", DEFAULT_LOG_DIR)
            DEFAULT_LOG_DIR.mkdir()
        if not DEFAULT_LOG_DIR.is_dir():
            errmsg = "Log file is not default and its parent dir doesn't exist"
            raise HandledError(errmsg)

        self.__logger.debug("Loaded config -> db_uri : %s", self.db_uri)

    def merge_with_args(self, **kwargs: Any) -> None:  # noqa: ANN401
        for key, value in kwargs.items():
            if value is not None:
                setattr(self, key, value)

    def save(self) -> None:
        data = {
            "db_uri": self.db_uri,
            "username": self.username,
            "password": self.password,
            "domain": self.domain,
            "aes_key": self.aes_key,
            "ccache_path": None if self.ccache_path is None else str(self.ccache_path),
            "auth_proto": str(self.auth_proto),
            "dc_ip": self.dc_ip,
            "dc_host": self.dc_host,
            "ldap_scheme": str(self.ldap_scheme),
            "dns_ip": self.dns_ip,
            "dns_proto": str(self.dns_proto),
            "hashes": self.hashes,
        }
        self.config_path.write_text(safe_dump(data))
