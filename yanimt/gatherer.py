"""Main module of Yanimt."""

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Concatenate, ParamSpec, TypeVar

from rich.console import Console
from rich.progress import Progress

from yanimt._config import AppConfig
from yanimt._database.manager import DatabaseManager
from yanimt._database.models import Computer, ComputerStatus, Domain, User
from yanimt._dns.main import resolve_dns
from yanimt._ldap.query import LdapQuery
from yanimt._smb.secrets_dump import SecretsDump
from yanimt._util.consts import PROGRESS_WIDGETS
from yanimt._util.logger import YanimtLogger, get_null_logger
from yanimt._util.smart_class import ADAuthentication, DCValues
from yanimt._util.types import AuthProto, Display, DnsProto, LdapScheme

P = ParamSpec("P")
T = TypeVar("T")


class YanimtGatherer:
    """Main class of Yanimt."""

    def __init__(
        self,
        config: AppConfig,
        console: Console | None = None,
        display: bool = True,
        live: bool = True,
        pager: bool = False,
        logger: YanimtLogger | None = None,
        debug: bool = False,
        username: str | None = None,
        password: str | None = None,
        domain: str | None = None,
        aes_key: str | None = None,
        ccache_path: Path | None = None,
        auth_proto: AuthProto = AuthProto.AUTO,
        dc_ip: str | None = None,
        dc_host: str | None = None,
        ldap_scheme: LdapScheme = LdapScheme.AUTO,
        dns_ip: str | None = None,
        dns_proto: DnsProto = DnsProto.AUTO,
        hashes: str | None = None,
        progress: Progress | None = None,
    ) -> None:
        """Init a Yanimt instance."""
        self.__config = config
        self.__now = datetime.now(tz=UTC)

        display_logger = get_null_logger() if logger is None else logger
        if console is None:
            display_console = Console(quiet=True)
            display_live_console = display_console
        else:
            display_console = console
            display_live_console = display_console if live else Console(quiet=True)
        if progress is None:
            progress = Progress(
                *PROGRESS_WIDGETS, transient=True, console=display_live_console
            )
        self.__display = Display(
            display_logger, display_console, display, pager, progress, debug
        )

        self.__database = DatabaseManager(self.__display, self.__config.db_uri)

        self.__ad_authentication = ADAuthentication(
            self.__display,
            auth_proto,
            username,
            password,
            hashes,
            aes_key,
            ccache_path,
            domain,
        )
        self.__dc_values = None

        self.__ldap_scheme = ldap_scheme

        self.__domain = self.__ad_authentication.user_domain
        self.__dc_host = dc_host
        self.__dc_ip = dc_ip
        self.__dns_ip = dns_ip
        self.__dns_proto = dns_proto

        self.__domain_sid = None
        self.__remoteOps = None
        self.__NTDSHashes = None

        self.__users = {}

    def init(self) -> None:
        self.__dc_values = DCValues(
            self.__display,
            self.__domain,
            self.__dc_host,
            self.__dc_ip,
            self.__dns_ip,
            self.__dns_proto,
        )
        dc = Computer(
            fqdn=self.__dc_values.host,
            ip=self.__dc_values.ip,
            status=ComputerStatus.DOMAIN_CONTROLLER,
        )
        self.__database.put_computer(dc)

    @staticmethod
    def __init_wrapper(
        funct: Callable[Concatenate[Any, P], T],
    ) -> Callable[Concatenate[Any, P], T]:
        def wrapper(self: Any, *args: P.args, **kwargs: P.kwargs) -> T:  # noqa: ANN401
            if self.__dc_values is None:
                self.init()
            return funct(self, *args, **kwargs)

        return wrapper

    @__init_wrapper
    def all_(self) -> None:
        """Run all the Yanimt workflow."""
        # Run
        with SecretsDump(
            self.__display,
            self.__database,
            self.__dc_values,  # pyright: ignore [reportArgumentType]
            self.__ad_authentication,
        ) as secrets_dump:
            domain_sid = secrets_dump.get_domain_sid()
            domain = Domain(sid=domain_sid, dns_name=self.__dc_values.domain)  # pyright: ignore [reportOptionalMemberAccess]
            self.__database.put_domain(domain)

            secrets_dump.pull_secrets()

        with LdapQuery(
            self.__display,
            self.__database,
            self.__dc_values,  # pyright: ignore [reportArgumentType]
            self.__ad_authentication,
            self.__ldap_scheme,
            domain_sid=domain_sid,
        ) as ldap_query:
            for computer in ldap_query.get_computers():
                resolve_dns(
                    self.__display,
                    self.__dc_values,  # pyright: ignore [reportArgumentType]
                    computer.fqdn,
                    database=self.__database,
                )
            Computer.print_tab(self.__display, self.__database.get_computers())

            User.print_tab(self.__display, ldap_query.get_users())
