from collections.abc import Generator

from impacket.ldap import ldap, ldapasn1  # pyright: ignore[reportAttributeAccessIssue]
from ldap3.protocol.formatters.formatters import format_sid

from yanimt._database.manager import DatabaseManager
from yanimt._database.models import Computer, User
from yanimt._ldap.main import Ldap
from yanimt._util import parse_uac, parse_windows_time
from yanimt._util.consts import ADMIN_GROUPS_SIDS
from yanimt._util.smart_class import ADAuthentication, DCValues
from yanimt._util.types import Display, LdapScheme


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
        self.users = False
        self.computers = False

    def __process_group(self, item: ldapasn1.SearchResultEntry) -> None:  # pyright: ignore[reportUnknownParameterType]
        if not isinstance(item, ldapasn1.SearchResultEntry):
            return
        group_dict = {}
        try:
            for attribute in item["attributes"]:
                if str(attribute["type"]) == "distinguishedName":
                    group_dict["distinguishedName"] = (
                        attribute["vals"][0].asOctets().decode("utf-8")
                    )
                if str(attribute["type"]) == "objectSid":
                    group_dict["objectSid"] = format_sid(
                        attribute["vals"][0].asOctets(),
                    )

            if (
                ("distinguishedName" in group_dict)
                and ("objectSid" in group_dict)
                and group_dict["objectSid"] in self.admin_groups
            ):
                self.admin_groups[group_dict["objectSid"]]["distinguishedName"] = (
                    group_dict["distinguishedName"]
                )
            self.display.progress.advance(self.display.progress.task_ids[0])
        except Exception as e:
            if self.display.debug:
                self.display.logger.exception(
                    "Skipping item, cannot process due to error"
                )
            else:
                self.display.logger.warning(
                    "Skipping item, cannot process due to error -> %s", e
                )

    def __recurse_process_group(self, item: ldapasn1.SearchResultEntry) -> None:  # pyright: ignore[reportUnknownParameterType]
        if not isinstance(item, ldapasn1.SearchResultEntry):
            return
        group_dict = {}
        try:
            for attribute in item["attributes"]:
                if str(attribute["type"]) == "distinguishedName":
                    group_dict["distinguishedName"] = (
                        attribute["vals"][0].asOctets().decode("utf-8")
                    )
            if "distinguishedName" in group_dict:
                self.admin_groups[self.__current_sid]["recurseMember"].add(
                    group_dict["distinguishedName"]
                )
            self.display.progress.advance(self.display.progress.task_ids[1])
        except Exception as e:
            if self.display.debug:
                self.display.logger.exception(
                    "Skipping item, cannot process due to error"
                )
            else:
                self.display.logger.warning(
                    "Skipping item, cannot process due to error -> %s", e
                )

    def __process_user(self, item: ldapasn1.SearchResultEntry) -> None:  # pyright: ignore[reportUnknownParameterType]
        if not isinstance(item, ldapasn1.SearchResultEntry):
            return
        user = User()
        try:
            for attribute in item["attributes"]:
                if str(attribute["type"]) == "sAMAccountName":
                    user.sam_account_name = (
                        attribute["vals"][0].asOctets().decode("utf-8")
                    )
                    if user.sam_account_name.endswith("$"):
                        return
                elif str(attribute["type"]) == "pwdLastSet":
                    user.pwd_last_set = parse_windows_time(
                        int(
                            attribute["vals"][0].asOctets().decode("utf-8"),
                        )
                    )
                elif str(attribute["type"]) == "mail":
                    user.mail = attribute["vals"][0].asOctets().decode("utf-8")
                elif str(attribute["type"]) == "objectSid":
                    user.sid = format_sid(attribute["vals"][0].asOctets())
                elif str(attribute["type"]) == "userAccountControl":
                    uac = int(attribute["vals"][0].asOctets().decode("utf-8"))
                    user.user_account_control = parse_uac(uac)
                elif str(attribute["type"]) == "servicePrincipalName":
                    user.service_principal_name = [
                        i.asOctets().decode("utf-8") for i in attribute["vals"]
                    ]
                elif str(attribute["type"]) == "accountExpires":
                    user.account_expires = parse_windows_time(
                        int(
                            attribute["vals"][0].asOctets().decode("utf-8"),
                        )
                    )
                elif str(attribute["type"]) == "memberOf":
                    user.member_of = [
                        i.asOctets().decode("utf-8") for i in attribute["vals"]
                    ]
                elif str(attribute["type"]) == "lastLogonTimestamp":
                    user.last_logon_timestamp = parse_windows_time(
                        int(
                            attribute["vals"][0].asOctets().decode("utf-8"),
                        )
                    )
                elif str(attribute["type"]) == "distinguishedName":
                    user.distinguished_name = (
                        attribute["vals"][0].asOctets().decode("utf-8")
                    )

            if (user.sam_account_name is None) or (user.sid is None):
                return

            if user.distinguished_name is not None:
                user.is_domain_admin = False
                user.is_entreprise_admin = False
                user.is_administrator = False
                for sid, group in self.admin_groups.items():
                    if user.distinguished_name in group["recurseMember"]:
                        if sid.endswith("-512"):
                            user.is_domain_admin = True
                        elif sid.endswith("-519"):
                            user.is_entreprise_admin = True
                        elif sid == "S-1-5-32-544":
                            user.is_administrator = True

            self.database.put_user(user)

            self.display.progress.advance(self.display.progress.task_ids[0])
        except Exception as e:
            if self.display.debug:
                self.display.logger.exception(
                    "Skipping item, cannot process due to error"
                )
            else:
                self.display.logger.warning(
                    "Skipping item, cannot process due to error -> %s", e
                )

    def __process_computer(self, item: ldapasn1.SearchResultEntry) -> None:  # pyright: ignore[reportUnknownParameterType]
        if not isinstance(item, ldapasn1.SearchResultEntry):
            return
        computer = Computer()
        try:
            for attribute in item["attributes"]:
                if str(attribute["type"]) == "dNSHostName":
                    computer.fqdn = (
                        attribute["vals"][0].asOctets().decode("utf-8").lower()
                    )

            if computer.fqdn is None:
                return

            self.database.put_computer(computer)

            self.display.progress.advance(self.display.progress.task_ids[0])
        except Exception as e:
            if self.display.debug:
                self.display.logger.exception(
                    "Skipping item, cannot process due to error"
                )
            else:
                self.display.logger.warning(
                    "Skipping item, cannot process due to error -> %s", e
                )

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
                        perRecordCallback=self.__process_group,
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
                            perRecordCallback=self.__recurse_process_group,
                        )
                    finally:
                        self.display.progress.remove_task(members_task)
                    self.display.progress.advance(main_task)
        finally:
            self.display.progress.remove_task(main_task)

    def pull_users(self) -> None:
        if self.connection is None:
            self.init_connect()

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
        self.users = True

    def pull_computers(self) -> None:
        if self.connection is None:
            self.init_connect()

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
                        "dNSHostName",
                    ],
                    searchControls=[self.sc],
                    perRecordCallback=self.__process_computer,
                )
        finally:
            self.display.progress.remove_task(task)
        self.computers = True

    def get_users(self) -> Generator[User]:
        if not self.users:
            self.pull_users()

        yield from self.database.get_users()

    def get_computers(self) -> Generator[Computer]:
        if not self.computers:
            self.pull_computers()

        yield from self.database.get_computers()
