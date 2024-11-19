import json
from collections.abc import Callable
from enum import StrEnum
from typing import Any, Optional

from rich.table import Table
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.types import UserDefinedType

from yanimt._util import auto_str
from yanimt._util.consts import TABLE_STYLE
from yanimt._util.types import Display, UacCodes

Base = declarative_base()


class ComputerStatus(StrEnum):
    READ_ONLY_DOMAIN_CONTROLLER = "Read only domain controller"
    DOMAIN_CONTROLLER = "Domain controller"
    SERVER = "Server"
    WORKSTATION = "Workstation"


class UacCodesArray(UserDefinedType[Any]):
    cache_ok = True

    def get_col_spec(self) -> str:
        return "TEXT"

    def bind_processor(  # pyright: ignore [reportIncompatibleMethodOverride]
        self, _dialect: Dialect
    ) -> Callable[[list[UacCodes] | None], str | None]:
        def process(value: list[UacCodes] | None) -> str | None:
            return json.dumps(value) if value is not None else None

        return process

    def result_processor(  # pyright: ignore [reportIncompatibleMethodOverride]
        self, _dialect: Dialect, _coltype: object
    ) -> Callable[[str | None], list[UacCodes] | None]:
        def process(value: str | None) -> list[UacCodes] | None:
            return (
                [UacCodes(code) for code in json.loads(value)]
                if value is not None
                else None
            )

        return process


class StringArray(UserDefinedType[Any]):
    cache_ok = True

    def get_col_spec(self) -> str:
        return "TEXT"

    def bind_processor(  # pyright: ignore [reportIncompatibleMethodOverride]
        self, _dialect: Dialect
    ) -> Callable[[list[str] | None], str | None]:
        def process(value: list[str] | None) -> str | None:
            return json.dumps(value) if value is not None else None

        return process

    def result_processor(  # pyright: ignore [reportIncompatibleMethodOverride]
        self, _dialect: Dialect, _coltype: object
    ) -> Callable[[str | None], list[str] | None]:
        def process(value: str | None) -> list[str] | None:
            return json.loads(value) if value is not None else None

        return process


@auto_str
class User(Base):
    __tablename__ = "users"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, User):
            return self.sid == other.sid  # pyright: ignore [reportAttributeAccessIssue]
        return False

    def __repr__(self) -> str:
        return (
            str(self.sam_account_name)
            if self.sam_account_name is not None
            else str(self.sid)
        )

    @staticmethod
    def print_tab(display: Display, users: list["User"]) -> None:
        table = Table(title="Users")
        table.add_column(
            "Sam account name", justify="center", style=TABLE_STYLE, no_wrap=True
        )
        table.add_column("SID", justify="center", style=TABLE_STYLE)
        table.add_column("Distinguished name", justify="center", style=TABLE_STYLE)
        table.add_column("Member of", justify="center", style=TABLE_STYLE)
        table.add_column("User account control", justify="center", style=TABLE_STYLE)
        table.add_column("Password last set", justify="center", style=TABLE_STYLE)
        table.add_column("Account expires", justify="center", style=TABLE_STYLE)
        table.add_column("Service principal name", justify="center", style=TABLE_STYLE)
        table.add_column("Mail", justify="center", style=TABLE_STYLE)
        table.add_column("NT Hash", justify="center", style=TABLE_STYLE)
        table.add_column("LM Hash", justify="center", style=TABLE_STYLE)
        table.add_column("Is domain admin", justify="center", style=TABLE_STYLE)
        table.add_column("Is entreprise admin", justify="center", style=TABLE_STYLE)
        table.add_column("Is administrator", justify="center", style=TABLE_STYLE)
        table.add_column("Last logon timestamp", justify="center", style=TABLE_STYLE)
        for user in users:
            table.add_row(
                user.sam_account_name,
                user.sid,
                user.distinguished_name,
                str(user.member_of),
                str(user.user_account_control),
                str(user.pwd_last_set),
                str(user.account_expires),
                str(user.service_principal_name),
                user.mail,
                user.nt_hash,
                user.lm_hash,
                str(user.is_domain_admin),
                str(user.is_entreprise_admin),
                str(user.is_administrator),
                str(user.last_logon_timestamp),
            )
        display.print_page(table)

    sid = Column(Text, primary_key=True)
    distinguished_name = Column(Text)
    member_of = Column(StringArray)
    user_account_control = Column(UacCodesArray)
    pwd_last_set = Column(DateTime(timezone=True))
    account_expires = Column(DateTime(timezone=True))
    sam_account_name = Column(Text)
    service_principal_name = Column(StringArray)
    mail = Column(Text)
    nt_hash = Column(Text)
    lm_hash = Column(Text)
    is_domain_admin = Column(Boolean)
    is_entreprise_admin = Column(Boolean)
    is_administrator = Column(Boolean)
    last_logon_timestamp = Column(DateTime(timezone=True))
    computer_id: Mapped[str | None] = mapped_column(ForeignKey("computers.fqdn"))
    computer: Mapped[Optional["Computer"]] = relationship(back_populates="user")


@auto_str
class Domain(Base):
    __tablename__ = "domains"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Domain):
            return self.sid == other.sid  # pyright: ignore [reportAttributeAccessIssue]
        return False

    def __repr__(self) -> str:
        return str(self.dns_name)

    sid = Column(Text, primary_key=True)
    dns_name = Column(Text)


@auto_str
class Computer(Base):
    __tablename__ = "computers"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Computer):
            return self.fqdn == other.fqdn  # pyright: ignore [reportAttributeAccessIssue]
        return False

    def __repr__(self) -> str:
        return str(self.fqdn)

    @staticmethod
    def print_tab(display: Display, computers: list["Computer"]) -> None:
        table = Table(title="Computers")
        table.add_column("FQDN", justify="center", style=TABLE_STYLE, no_wrap=True)
        table.add_column("IP", justify="center", style=TABLE_STYLE)
        table.add_column("Status", justify="center", style=TABLE_STYLE)
        for computer in computers:
            table.add_row(computer.fqdn, computer.ip, computer.status)
        display.print_page(table)

    fqdn = Column(Text, primary_key=True)
    ip = Column(Text)
    operating_system = Column(Text)
    status = Column(SqlEnum(ComputerStatus))
    user: Mapped["User"] = relationship(back_populates="computer")


@auto_str
class Group(Base):
    __tablename__ = "groups"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Group):
            return self.sid == other.sid  # pyright: ignore [reportAttributeAccessIssue]
        return False

    def __repr__(self) -> str:
        return (
            str(self.sam_account_name)
            if self.sam_account_name is not None
            else str(self.sid)
        )

    @staticmethod
    def print_tab(display: Display, groups: list["Group"]) -> None:
        table = Table(title="Groups")
        table.add_column(
            "Sam account name", justify="center", style=TABLE_STYLE, no_wrap=True
        )
        table.add_column("SID", justify="center", style=TABLE_STYLE)
        table.add_column("Distinguished name", justify="center", style=TABLE_STYLE)
        table.add_column("Members", justify="center", style=TABLE_STYLE)
        for group in groups:
            table.add_row(
                group.sam_account_name,
                group.sid,
                group.distinguished_name,
                str(group.members),
            )
        display.print_page(table)

    sid = Column(Text, primary_key=True)
    distinguished_name = Column(Text)
    members = Column(StringArray)
    sam_account_name = Column(Text)
