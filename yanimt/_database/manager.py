from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from yanimt._database.models import (
    Base,
    Computer,
    Domain,
    Group,
    OrganisationalUnit,
    User,
)
from yanimt._util.consts import BATCH_SIZE
from yanimt._util.types import Display


class DatabaseManager:
    """Class that manages the database."""

    def __init__(self, display: Display, db_uri: str) -> None:
        self.display = display
        self.engine = create_engine(db_uri)
        Base.metadata.create_all(bind=self.engine)
        self.session_maker = sessionmaker(self.engine, expire_on_commit=False)

    def clear(self) -> None:
        Base.metadata.drop_all(bind=self.engine)

    def put_user(self, user: User) -> None:
        with self.session_maker.begin() as session:
            return session.merge(user)

    def get_users(self) -> Generator[User]:
        with self.session_maker.begin() as session:
            yield from (
                session.query(User)
                .filter(User.computer == None)  # noqa: E711
                .order_by(User.sam_account_name)
                .yield_per(BATCH_SIZE)
            )

    def get_user(self, sid: str) -> User:
        with self.session_maker.begin() as session:
            return session.query(User).get(sid)

    def put_domain(self, domain: Domain) -> None:
        with self.session_maker.begin() as session:
            return session.merge(domain)

    def get_domain(self) -> Domain:
        with self.session_maker.begin() as session:
            return session.query(Domain).one_or_none()

    def put_computer(self, computer: Computer) -> None:
        with self.session_maker.begin() as session:
            return session.merge(computer)

    def get_computers(self) -> Generator[Computer]:
        with self.session_maker.begin() as session:
            yield from (
                session.query(Computer).order_by(Computer.fqdn).yield_per(BATCH_SIZE)
            )

    def get_computer(self, fqdn: str) -> Computer:
        with self.session_maker.begin() as session:
            return session.query(Computer).get(fqdn)

    def put_group(self, group: Group) -> None:
        with self.session_maker.begin() as session:
            return session.merge(group)

    def get_groups(self) -> Generator[Group]:
        with self.session_maker.begin() as session:
            yield from (
                session.query(Group)
                .order_by(Group.sam_account_name)
                .yield_per(BATCH_SIZE)
            )

    def get_group(self, sid: str) -> Group:
        with self.session_maker.begin() as session:
            return session.query(Group).get(sid)

    def put_organisational_unit(self, organisational_unit: OrganisationalUnit) -> None:
        with self.session_maker.begin() as session:
            return session.merge(organisational_unit)

    def get_organisational_units(self) -> Generator[OrganisationalUnit]:
        with self.session_maker.begin() as session:
            yield from (
                session.query(OrganisationalUnit)
                .order_by(OrganisationalUnit.name)
                .yield_per(BATCH_SIZE)
            )

    def get_organisational_unit(self, distinguished_name: str) -> OrganisationalUnit:
        with self.session_maker.begin() as session:
            return session.query(OrganisationalUnit).get(distinguished_name)
