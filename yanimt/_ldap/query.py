from datetime import datetime
from typing import Optional

from impacket.ldap import ldap, ldapasn1  # pyright: ignore[reportAttributeAccessIssue]
from ldap3.protocol.formatters.formatters import format_sid

from yanimt._database.manager import DatabaseManager
from yanimt._database.models import (
    Computer,
    ComputerStatus,
    Group,
    OrganisationalUnit,
    User,
)
from yanimt._ldap.main import Ldap
from yanimt._util import parse_uac, parse_windows_time
from yanimt._util.consts import ADMIN_GROUPS_SIDS
from yanimt._util.smart_class import ADAuthentication, DCValues
from yanimt._util.types import Display, LdapScheme, UacCodes


class LdapResult:
    def __init__(
        self,
        distinguished_name: str | None = None,
        name: str | None = None,
        sid: str | None = None,
        members: list[str] | None = None,
        sam_account_name: str | None = None,
        pwd_last_set: datetime | None = None,
        mail: str | None = None,
        user_account_control: list[UacCodes] | None = None,
        service_principal_name: list[str] | None = None,
        account_expires: datetime | None = None,
        member_of: list[str] | None = None,
        last_logon_timestamp: datetime | None = None,
        fqdn: str | None = None,
        operating_system: str | None = None,
    ) -> None:
        self.distinguished_name = distinguished_name
        self.name = name
        self.sid = sid
        self.members = members
        self.sam_account_name = sam_account_name
        self.pwd_last_set = pwd_last_set
        self.mail = mail
        self.user_account_control = user_account_control
        self.service_principal_name = service_principal_name
        self.account_expires = account_expires
        self.member_of = member_of
        self.last_logon_timestamp = last_logon_timestamp
        self.fqdn = fqdn
        self.operating_system = operating_system

    def get_group(self) -> Group:
        return Group(
            distinguished_name=self.distinguished_name,
            sid=self.sid,
            members=self.members,
            sam_account_name=self.sam_account_name,
        )

    def get_organisational_unit(self) -> OrganisationalUnit:
        return OrganisationalUnit(
            distinguished_name=self.distinguished_name,
            name=self.name,
        )

    def get_user(self) -> User:
        return User(
            sam_account_name=self.sam_account_name,
            pwd_last_set=self.pwd_last_set,
            mail=self.mail,
            sid=self.sid,
            user_account_control=None
            if self.user_account_control is None
            else self.user_account_control.copy(),
            service_principal_name=None
            if self.service_principal_name is None
            else self.service_principal_name.copy(),
            account_expires=self.account_expires,
            member_of=None if self.member_of is None else self.member_of.copy(),
            last_logon_timestamp=self.last_logon_timestamp,
            distinguished_name=self.distinguished_name,
        )

    def get_computer(self) -> Computer:
        user = User(
            sam_account_name=self.sam_account_name,
            pwd_last_set=self.pwd_last_set,
            mail=self.mail,
            sid=self.sid,
            user_account_control=None
            if self.user_account_control is None
            else self.user_account_control.copy(),
            service_principal_name=None
            if self.service_principal_name is None
            else self.service_principal_name.copy(),
            account_expires=self.account_expires,
            member_of=None if self.member_of is None else self.member_of.copy(),
            last_logon_timestamp=self.last_logon_timestamp,
            distinguished_name=self.distinguished_name,
        )
        computer = Computer(
            fqdn=self.fqdn,
            operating_system=self.operating_system,
            user=user,
        )
        if (
            user.user_account_control is not None
            and UacCodes.SERVER_TRUST_ACCOUNT in user.user_account_control
        ):
            computer.status = ComputerStatus.DOMAIN_CONTROLLER
        elif (
            user.user_account_control is not None
            and UacCodes.PARTIAL_SECRETS_ACCOUNT in user.user_account_control
        ):
            computer.status = ComputerStatus.READ_ONLY_DOMAIN_CONTROLLER
        elif (
            computer.operating_system is not None
            and "server" in computer.operating_system.lower()
        ):
            computer.status = ComputerStatus.SERVER
        elif computer.operating_system is not None:
            computer.status = ComputerStatus.WORKSTATION
        return computer

    @staticmethod
    def from_search_entry(
        display: Display,
        item: ldapasn1.SearchResultEntry,  # pyright: ignore [reportUnknownParameterType]
    ) -> Optional["LdapResult"]:
        if not isinstance(item, ldapasn1.SearchResultEntry):
            return None

        return_obj = LdapResult()
        try:
            for attribute in item["attributes"]:
                match str(attribute["type"]):
                    case "distinguishedName":
                        return_obj.distinguished_name = (
                            attribute["vals"][0].asOctets().decode("utf-8")
                        )
                    case "name":
                        return_obj.name = (
                            attribute["vals"][0].asOctets().decode("utf-8")
                        )
                    case "objectSid":
                        return_obj.sid = format_sid(
                            attribute["vals"][0].asOctets(),
                        )
                    case "member":
                        return_obj.members = [
                            i.asOctets().decode("utf-8") for i in attribute["vals"]
                        ]
                    case "sAMAccountName":
                        return_obj.sam_account_name = (
                            attribute["vals"][0].asOctets().decode("utf-8")
                        )
                    case "pwdLastSet":
                        return_obj.pwd_last_set = parse_windows_time(
                            int(
                                attribute["vals"][0].asOctets().decode("utf-8"),
                            )
                        )
                    case "mail":
                        return_obj.mail = (
                            attribute["vals"][0].asOctets().decode("utf-8")
                        )
                    case "userAccountControl":
                        uac = int(attribute["vals"][0].asOctets().decode("utf-8"))
                        return_obj.user_account_control = parse_uac(uac)
                    case "servicePrincipalName":
                        return_obj.service_principal_name = [
                            i.asOctets().decode("utf-8") for i in attribute["vals"]
                        ]
                    case "accountExpires":
                        return_obj.account_expires = parse_windows_time(
                            int(
                                attribute["vals"][0].asOctets().decode("utf-8"),
                            )
                        )
                    case "memberOf":
                        return_obj.member_of = [
                            i.asOctets().decode("utf-8") for i in attribute["vals"]
                        ]
                    case "lastLogonTimestamp":
                        return_obj.last_logon_timestamp = parse_windows_time(
                            int(
                                attribute["vals"][0].asOctets().decode("utf-8"),
                            )
                        )
                    case "dNSHostName":
                        return_obj.fqdn = (
                            attribute["vals"][0].asOctets().decode("utf-8").lower()
                        )
                    case "operatingSystem":
                        return_obj.operating_system = (
                            attribute["vals"][0].asOctets().decode("utf-8")
                        )
                    case _:
                        pass
        except Exception as e:
            if display.debug:
                display.logger.exception("Skipping item, cannot process due to error")
            else:
                display.logger.warning(
                    "Skipping item, cannot process due to error -> %s", e
                )
        else:
            return return_obj


class LdapQuery(Ldap):
    def __init__(
        self,
        display: Display,
        database: DatabaseManager,
        dc_values: DCValues,
        ad_authentication: ADAuthentication,
        scheme: LdapScheme,
        domain_sid: str,
    ) -> None:
        super().__init__(display, database, dc_values, ad_authentication, scheme)

        self.sc = ldap.SimplePagedResultsControl(size=1000, criticality=True)
        self.admin_groups = {
            admin_group.format(domain_sid=domain_sid): {"recurseMember": set()}
            for admin_group in ADMIN_GROUPS_SIDS
        }
        self.users = None
        self.computers = None
        self.groups = None
        self.organisational_units = None

        self.__current_sid = None
        self.__current_organisational_unit = None

    def __process_organisational_unit_members(
        self,
        item: ldapasn1.SearchResultEntry,  # pyright: ignore [reportUnknownParameterType]
    ) -> None:
        ldap_result = LdapResult.from_search_entry(self.display, item)
        if ldap_result is None:
            return
        distinguished_name = ldap_result.distinguished_name
        if distinguished_name is None:
            return

        if distinguished_name not in self.__current_organisational_unit.members:  # pyright: ignore[reportOptionalMemberAccess]
            self.__current_organisational_unit.members.append(distinguished_name)  # pyright: ignore[reportOptionalMemberAccess]
        self.display.progress.advance(self.display.progress.task_ids[0])

    def __process_organisational_unit(self, item: ldapasn1.SearchResultEntry) -> None:  # pyright: ignore[reportUnknownParameterType]
        ldap_result = LdapResult.from_search_entry(self.display, item)
        if ldap_result is None:
            return
        ou = ldap_result.get_organisational_unit()
        if ou.distinguished_name is None:
            return

        self.organisational_units[ou.distinguished_name] = (  # pyright: ignore [reportOptionalSubscript]
            self.database.put_organisational_unit(ou)
        )
        self.display.progress.advance(self.display.progress.task_ids[0])

    def __process_group(self, item: ldapasn1.SearchResultEntry) -> None:  # pyright: ignore[reportUnknownParameterType]
        ldap_result = LdapResult.from_search_entry(self.display, item)
        if ldap_result is None:
            return
        group = ldap_result.get_group()
        if group.sid is None:
            return

        self.groups[group.sid] = self.database.put_group(group)  # pyright: ignore[reportOptionalSubscript]
        self.display.progress.advance(self.display.progress.task_ids[0])

    def __process_admin_group(self, item: ldapasn1.SearchResultEntry) -> None:  # pyright: ignore[reportUnknownParameterType]
        ldap_result = LdapResult.from_search_entry(self.display, item)
        if ldap_result is None:
            return

        if (
            ldap_result.distinguished_name is not None
            and ldap_result.sid is not None
            and ldap_result.sid in self.admin_groups
        ):
            self.admin_groups[ldap_result.sid]["distinguishedName"] = (  # pyright: ignore[reportArgumentType]
                ldap_result.distinguished_name
            )
        self.display.progress.advance(self.display.progress.task_ids[0])

    def __recurse_process_admin_group(self, item: ldapasn1.SearchResultEntry) -> None:  # pyright: ignore[reportUnknownParameterType]
        ldap_result = LdapResult.from_search_entry(self.display, item)
        if ldap_result is None:
            return
        distinguished_name = ldap_result.distinguished_name
        if distinguished_name is not None:
            self.admin_groups[self.__current_sid]["recurseMember"].add(  # pyright: ignore[reportArgumentType]
                distinguished_name
            )
        self.display.progress.advance(self.display.progress.task_ids[1])

    def __process_user(self, item: ldapasn1.SearchResultEntry) -> None:  # pyright: ignore[reportUnknownParameterType]
        ldap_result = LdapResult.from_search_entry(self.display, item)
        if ldap_result is None:
            return
        user = ldap_result.get_user()
        if user.sid is None:
            return

        if user.distinguished_name is not None:
            user.is_orivileged = False
            for group in self.admin_groups.values():
                if user.distinguished_name in group["recurseMember"]:
                    user.is_privileged = True
                    break

        self.users[user.sid] = self.database.put_user(user)  # pyright: ignore[reportOptionalSubscript]
        self.display.progress.advance(self.display.progress.task_ids[0])

    def __process_computer(self, item: ldapasn1.SearchResultEntry) -> None:  # pyright: ignore[reportUnknownParameterType]
        ldap_result = LdapResult.from_search_entry(self.display, item)
        if ldap_result is None:
            return
        computer = ldap_result.get_computer()
        if computer.fqdn is None:
            return

        self.computers[computer.fqdn] = self.database.put_computer(computer)  # pyright: ignore[reportOptionalSubscript]
        self.display.progress.advance(self.display.progress.task_ids[0])

    def __pull_admins(self) -> None:
        task = self.display.progress.add_task(
            "[blue]Querying ldap admin groups[/blue]", total=3
        )
        try:
            with self.display.progress:
                self.display.logger.opsec(
                    "[%s -> %s] Querying base admin groups",
                    self.scheme.value.upper(),
                    self.dc_values.ip,
                )
                for sid in self.admin_groups:
                    search_filter = f"(objectSid={sid})"
                    self.connection.search(  # pyright: ignore [reportOptionalMemberAccess]
                        searchFilter=search_filter,
                        attributes=["distinguishedName", "objectSid"],
                        searchControls=[self.sc],
                        perRecordCallback=self.__process_admin_group,
                    )
        finally:
            self.display.progress.remove_task(task)

    def __pull_recursive_admins(self) -> None:
        main_task = self.display.progress.add_task(
            "[blue]Recurse ldap admin groups[/blue]", total=3
        )
        try:
            with self.display.progress:
                self.display.logger.opsec(
                    "[%s -> %s] Querying admin groups recursively",
                    self.scheme.value.upper(),
                    self.dc_values.ip,
                )
                for sid, group in self.admin_groups.items():
                    if "distinguishedName" not in group:
                        self.display.logger.warning(
                            "A default administrative group doesn't exist -> %s", sid
                        )
                    dn = group["distinguishedName"]
                    self.__current_sid = sid
                    encoded_dn = "".join(f"\\{i:02x}" for i in dn.encode("utf-8"))  # pyright: ignore [reportAttributeAccessIssue]
                    search_filter = f"(&(memberOf:1.2.840.113556.1.4.1941:={encoded_dn})(objectCategory=user))"
                    members_task = self.display.progress.add_task(
                        f"[blue]Recurse ldap members for {dn}[/blue]", total=None
                    )
                    try:
                        self.connection.search(  # pyright: ignore [reportOptionalMemberAccess]
                            searchFilter=search_filter,
                            attributes=["distinguishedName"],
                            searchControls=[self.sc],
                            perRecordCallback=self.__recurse_process_admin_group,
                        )
                    finally:
                        self.display.progress.remove_task(members_task)
                    self.display.progress.advance(main_task)
        finally:
            self.display.progress.remove_task(main_task)

    def pull_users(self) -> None:
        if self.connection is None:
            self.init_connect()

        self.users = {}
        self.__pull_admins()
        self.__pull_recursive_admins()
        search_filter = "(&(objectCategory=person)(objectClass=user))"
        task = self.display.progress.add_task(
            "[blue]Querying ldap users[/blue]",
            total=None,
        )
        try:
            with self.display.progress:
                self.display.logger.opsec(
                    "[%s -> %s] Querying ldap users",
                    self.scheme.value.upper(),
                    self.dc_values.ip,
                )
                self.connection.search(  # pyright: ignore [reportOptionalMemberAccess]
                    searchFilter=search_filter,
                    attributes=[
                        "sAMAccountName",
                        "pwdLastSet",
                        "mail",
                        "objectSid",
                        "userAccountControl",
                        "servicePrincipalName",
                        "accountExpires",
                        "memberOf",
                        "lastLogonTimestamp",
                        "distinguishedName",
                    ],
                    searchControls=[self.sc],
                    perRecordCallback=self.__process_user,
                )
        finally:
            self.display.progress.remove_task(task)

    def pull_computers(self) -> None:
        if self.connection is None:
            self.init_connect()

        self.computers = {}
        search_filter = "(objectCategory=Computer)"
        task = self.display.progress.add_task(
            "[blue]Querying ldap computers[/blue]",
            total=None,
        )
        try:
            with self.display.progress:
                self.display.logger.opsec(
                    "[%s -> %s] Querying ldap computers",
                    self.scheme.value.upper(),
                    self.dc_values.ip,
                )
                self.connection.search(  # pyright: ignore [reportOptionalMemberAccess]
                    searchFilter=search_filter,
                    attributes=[
                        "sAMAccountName",
                        "pwdLastSet",
                        "mail",
                        "objectSid",
                        "userAccountControl",
                        "servicePrincipalName",
                        "accountExpires",
                        "memberOf",
                        "lastLogonTimestamp",
                        "distinguishedName",
                        "dNSHostName",
                        "operatingSystem",
                    ],
                    searchControls=[self.sc],
                    perRecordCallback=self.__process_computer,
                )
        finally:
            self.display.progress.remove_task(task)

    def pull_groups(self) -> None:
        if self.connection is None:
            self.init_connect()

        self.groups = {}
        search_filter = "(objectClass=group)"
        task = self.display.progress.add_task(
            "[blue]Querying ldap groups[/blue]",
            total=None,
        )
        try:
            with self.display.progress:
                self.display.logger.opsec(
                    "[%s -> %s] Querying ldap groups",
                    self.scheme.value.upper(),
                    self.dc_values.ip,
                )
                self.connection.search(  # pyright: ignore [reportOptionalMemberAccess]
                    searchFilter=search_filter,
                    attributes=[
                        "sAMAccountName",
                        "objectSid",
                        "distinguishedName",
                        "member",
                    ],
                    searchControls=[self.sc],
                    perRecordCallback=self.__process_group,
                )
        finally:
            self.display.progress.remove_task(task)

    def pull_organisational_units(self) -> None:
        if self.connection is None:
            self.init_connect()

        self.organisational_units = {}
        search_filter = "(objectClass=organizationalUnit)"
        task = self.display.progress.add_task(
            "[blue]Querying ldap organisational units[/blue]",
            total=None,
        )
        try:
            with self.display.progress:
                self.display.logger.opsec(
                    "[%s -> %s] Querying ldap organisational units",
                    self.scheme.value.upper(),
                    self.dc_values.ip,
                )
                self.connection.search(  # pyright: ignore [reportOptionalMemberAccess]
                    searchFilter=search_filter,
                    attributes=[
                        "name",
                        "distinguishedName",
                    ],
                    searchControls=[self.sc],
                    perRecordCallback=self.__process_organisational_unit,
                )
        finally:
            self.display.progress.remove_task(task)
        task = self.display.progress.add_task(
            "[blue]Querying ldap organisational units members[/blue]",
            total=None,
        )
        try:
            for ou in self.organisational_units.values():
                self.__current_organisational_unit = ou
                self.__current_organisational_unit.members = []
                search_filter = f"(!(distinguishedName={ou.distinguished_name}))"
                with self.display.progress:
                    self.display.logger.opsec(
                        "[%s -> %s] Querying ldap organisational units members",
                        self.scheme.value.upper(),
                        self.dc_values.ip,
                    )
                    self.connection.search(  # pyright: ignore [reportOptionalMemberAccess]
                        searchFilter=search_filter,
                        searchBase=ou.distinguished_name,
                        attributes=[
                            "distinguishedName",
                        ],
                        searchControls=[self.sc],
                        perRecordCallback=self.__process_organisational_unit_members,
                    )
                self.database.put_organisational_unit(
                    self.__current_organisational_unit
                )
        finally:
            self.display.progress.remove_task(task)

    def get_users(self) -> dict[str, User]:
        if self.users is None:
            self.pull_users()

        return self.users  # pyright: ignore [reportReturnType]

    def get_computers(self) -> dict[str, Computer]:
        if self.computers is None:
            self.pull_computers()

        return self.computers  # pyright: ignore [reportReturnType]

    def get_groups(self) -> dict[str, Group]:
        if self.groups is None:
            self.pull_groups()

        return self.groups  # pyright: ignore [reportReturnType]

    def get_organisational_units(self) -> dict[str, OrganisationalUnit]:
        if self.organisational_units is None:
            self.pull_organisational_units()

        return self.organisational_units  # pyright: ignore [reportReturnType]

    def display_users(self) -> None:
        if self.users is None:
            self.pull_users()

        User.print_tab(self.display, self.users.values())  # pyright: ignore [reportOptionalMemberAccess]

    def display_computers(self) -> None:
        if self.computers is None:
            self.pull_computers()

        Computer.print_tab(self.display, self.computers.values())  # pyright: ignore [reportOptionalMemberAccess]

    def display_groups(self) -> None:
        if self.groups is None:
            self.pull_groups()

        Group.print_tab(self.display, self.groups.values())  # pyright: ignore [reportOptionalMemberAccess]

    def display_organisational_units(self) -> None:
        if self.organisational_units is None:
            self.pull_organisational_units()

        OrganisationalUnit.print_tab(self.display, self.organisational_units.values())  # pyright: ignore [reportOptionalMemberAccess]
