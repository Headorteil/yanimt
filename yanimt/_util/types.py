import pydoc
from enum import Enum, IntEnum, StrEnum, auto, unique
from typing import Any

from rich.console import Console
from rich.pager import Pager
from rich.progress import Progress

from yanimt._util.logger import YanimtLogger


@unique
class UacCodes(IntEnum):
    SCRIPT = 0x0001
    ACCOUNTDISABLE = 0x0002
    HOMEDIR_REQUIRED = 0x0008
    LOCKOUT = 0x0010
    PASSWD_NOTREQD = 0x0020
    PASSWD_CANT_CHANGE = 0x0040
    ENCRYPTED_TEXT_PWD_ALLOWED = 0x0080
    TEMP_DUPLICATE_ACCOUNT = 0x0100
    NORMAL_ACCOUNT = 0x0200
    INTERDOMAIN_TRUST_ACCOUNT = 0x0800
    WORKSTATION_TRUST_ACCOUNT = 0x1000
    SERVER_TRUST_ACCOUNT = 0x2000
    DONT_EXPIRE_PASSWORD = 0x10000
    MNS_LOGON_ACCOUNT = 0x20000
    SMARTCARD_REQUIRED = 0x40000
    TRUSTED_FOR_DELEGATION = 0x80000
    NOT_DELEGATED = 0x100000
    USE_DES_KEY_ONLY = 0x200000
    DONT_REQ_PREAUTH = 0x400000
    PASSWORD_EXPIRED = 0x800000
    TRUSTED_TO_AUTH_FOR_DELEGATION = 0x1000000
    PARTIAL_SECRETS_ACCOUNT = 0x04000000

    def __repr__(self) -> str:
        return self.name


class SmbState(Enum):
    CONNECT = auto()
    REMOTEOPS = auto()


class AuthProto(StrEnum):
    KERBEROS = "kerberos"
    NTLM = "ntlm"
    AUTO = "auto"


class LdapScheme(StrEnum):
    LDAP = "ldap"
    LDAPS = "ldaps"
    AUTO = "auto"


class DnsProto(StrEnum):
    TCP = "tcp"
    UDP = "udp"
    AUTO = "auto"


class LessPager(Pager):
    def _pager(self, content: str) -> None:
        pydoc.pipepager(content, "less -S +g -R")

    def show(self, content: str) -> None:
        self._pager(content)


class Display:
    def __init__(
        self,
        logger: YanimtLogger,
        console: Console,
        display: bool,
        pager: bool,
        progress: Progress,
        debug: bool,
    ) -> None:
        self.pager = pager
        self.logger = logger
        self.console = console
        self.display = display
        self.progress = progress
        self.debug = debug

    def print_page(self, obj: Any) -> None:  # noqa: ANN401
        if not self.display:
            return
        extra_width = obj._extra_width  # noqa: SLF001
        max_width = sum(
            obj._calculate_column_widths(  # noqa: SLF001
                self.console,
                self.console.options.update_width(
                    self.console.options.max_width - extra_width
                ),
            )
        )
        measurements = [
            obj._measure_column(  # noqa: SLF001
                self.console, self.console.options.update_width(max_width), column
            )
            for column in obj.columns
        ]
        minimum_width = (
            sum(measurement.minimum for measurement in measurements) + extra_width
        )
        too_large = minimum_width > self.console.options.max_width
        if self.pager and too_large:
            self.logger.info("Table too large, printing it in less")
            pager_console = Console(width=1000)
            with pager_console.pager(styles=True, pager=LessPager()):
                pager_console.print(obj)
        else:
            obj.expand = True
            if too_large:
                self.console.print(
                    'Table too large, you should enable pager with "yanimt -p"'
                )
            self.console.print(obj)
