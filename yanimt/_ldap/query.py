from impacket.ldap import ldap, ldapasn1  # pyright: ignore[reportAttributeAccessIssue]
from ldap3.protocol.formatters.formatters import format_sid

from yanimt._database.manager import DatabaseManager
from yanimt._database.models import Computer, ComputerStatus, Group, User
from yanimt._ldap.main import Ldap
from yanimt._util import parse_uac, parse_windows_time
from yanimt._util.consts import ADMIN_GROUPS_SIDS
from yanimt._util.smart_class import ADAuthentication, DCValues
from yanimt._util.types import Display, LdapScheme, UacCodes


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

    def __process_group(self, item: ldapasn1.SearchResultEntry) -> None:  # pyright: ignore[reportUnknownParameterType]
        if not isinstance(item, ldapasn1.SearchResultEntry):
            return
        group = Group()
        try:
            for attribute in item["attributes"]:
                if str(attribute["type"]) == "distinguishedName":
                    group.distinguished_name = (
                        attribute["vals"][0].asOctets().decode("utf-8")
                    )
                elif str(attribute["type"]) == "objectSid":
                    group.sid = format_sid(
                        attribute["vals"][0].asOctets(),
                    )
                elif str(attribute["type"]) == "member":
                    group.members = [
                        i.asOctets().decode("utf-8") for i in attribute["vals"]
                    ]
                elif str(attribute["type"]) == "sAMAccountName":
                    group.sam_account_name = (
                        attribute["vals"][0].asOctets().decode("utf-8")
                    )

            if group.sid is None:
                return

            self.groups[group.sid] = self.database.put_group(group)  # pyright: ignore[reportOptionalSubscript]

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

    def __process_admin_group(self, item: ldapasn1.SearchResultEntry) -> None:  # pyright: ignore[reportUnknownParameterType]
        if not isinstance(item, ldapasn1.SearchResultEntry):
            return
        group_dict = {}
        try:
            for attribute in item["attributes"]:
                if str(attribute["type"]) == "distinguishedName":
                    group_dict["distinguishedName"] = (
                        attribute["vals"][0].asOctets().decode("utf-8")
                    )
                elif str(attribute["type"]) == "objectSid":
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

    def __recurse_process_admin_group(self, item: ldapasn1.SearchResultEntry) -> None:  # pyright: ignore[reportUnknownParameterType]
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

            if user.sid is None:
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

            self.users[user.sid] = self.database.put_user(user)  # pyright: ignore[reportOptionalSubscript]

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
        user = User()
        computer = Computer()
        try:
            for attribute in item["attributes"]:
                if str(attribute["type"]) == "sAMAccountName":
                    user.sam_account_name = (
                        attribute["vals"][0].asOctets().decode("utf-8")
                    )
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

                elif str(attribute["type"]) == "dNSHostName":
                    computer.fqdn = (
                        attribute["vals"][0].asOctets().decode("utf-8").lower()
                    )
                elif str(attribute["type"]) == "operatingSystem":
                    computer.operating_system = (
                        attribute["vals"][0].asOctets().decode("utf-8")
                    )

            if user.sid is not None:
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
                computer.user = user
            else:
                computer.user = None

            if computer.fqdn is None:
                return

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

            self.computers[computer.fqdn] = self.database.put_computer(computer)  # pyright: ignore[reportOptionalSubscript]

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
                        "distinguishedName",
                        "objectSid",
                        "member",
                    ],
                    searchControls=[self.sc],
                    perRecordCallback=self.__process_group,
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

    def get_groups(self) -> dict[str, "Group"]:
        if self.groups is None:
            self.pull_groups()

        return self.groups  # pyright: ignore [reportReturnType]

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
