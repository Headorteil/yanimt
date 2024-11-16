from typing import Self

from impacket.ldap import ldap  # pyright: ignore [reportAttributeAccessIssue]

from yanimt._database.manager import DatabaseManager
from yanimt._util.exceptions import HandledError
from yanimt._util.smart_class import ADAuthentication, DCValues
from yanimt._util.types import AuthProto, Display, LdapScheme


class Ldap:
    def __init__(
        self,
        display: Display,
        database: DatabaseManager,
        dc_values: DCValues,
        ad_authentication: ADAuthentication,
        scheme: LdapScheme,
    ) -> None:
        self.display = display
        self.database = database
        self.dc_values = dc_values
        self.ad_authentication = ad_authentication
        self.scheme = scheme

        self.connection = None

    def __enter__(self) -> Self:
        if self.connection is None:
            self.init_connect()
        return self

    def __exit__(self, *_: object) -> None:
        self.cleanup()

    def __ldap_login(self) -> None:
        if self.connection is None:
            errmsg = "Can't login before connecting"
            raise HandledError(errmsg)
        if self.ad_authentication.auth_proto is AuthProto.KERBEROS:
            self.display.logger.opsec(
                "[%s (KERBEROS) -> %s] Authenticate to %s with Kerberos",
                self.scheme.value.upper(),
                self.dc_values.ip,
                self.scheme.value,
            )
            self.connection.kerberosLogin(
                self.ad_authentication.username,
                self.ad_authentication.password,
                domain=self.dc_values.domain,
                lmhash=self.ad_authentication.lm_hash,
                nthash=self.ad_authentication.nt_hash,
                aesKey=self.ad_authentication.aes_key,
                kdcHost=self.dc_values.ip,
                TGT=self.ad_authentication.tgt,
                useCache=False,
            )
        elif self.ad_authentication.auth_proto is AuthProto.NTLM:
            self.display.logger.opsec(
                "[%s (NTLM) -> %s] Authenticate to %s with NTLM",
                self.scheme.value.upper(),
                self.dc_values.ip,
                self.scheme.value,
            )
            self.connection.login(
                user=self.ad_authentication.username,
                password=self.ad_authentication.password,
                domain=self.dc_values.domain,
                lmhash=self.ad_authentication.lm_hash,
                nthash=self.ad_authentication.nt_hash,
            )
        else:
            self.ad_authentication.auth_proto = AuthProto.NTLM
            self.display.logger.opsec(
                "[%s (NTLM) -> %s] Authenticate to %s with NTLM",
                self.scheme.value.upper(),
                self.dc_values.ip,
                self.scheme.value,
            )
            try:
                self.connection.login(
                    user=self.ad_authentication.username,
                    password=self.ad_authentication.password,
                    domain=self.dc_values.domain,
                    lmhash=self.ad_authentication.lm_hash,
                    nthash=self.ad_authentication.nt_hash,
                )
            except ldap.LDAPSessionError as e:
                if str(e).find("NTLMAuthNegotiate") >= 0:
                    self.display.logger.debug(
                        "Authenticate to %s with NTLM failed, tying Kerberos",
                        self.scheme.value,
                    )
                    self.ad_authentication.auth_proto = AuthProto.KERBEROS
                    self.display.logger.opsec(
                        "[%s (KERBEROS) -> %s] Authenticate to %s with Kerberos",
                        self.scheme.value.upper(),
                        self.dc_values.ip,
                        self.scheme.value,
                    )
                    self.connection.kerberosLogin(
                        self.ad_authentication.username,
                        self.ad_authentication.password,
                        domain=self.dc_values.domain,
                        lmhash=self.ad_authentication.lm_hash,
                        nthash=self.ad_authentication.nt_hash,
                        aesKey=self.ad_authentication.aes_key,
                        kdcHost=self.dc_values.ip,
                        TGT=self.ad_authentication.tgt,
                        useCache=False,
                    )
                else:
                    raise

    def cleanup(self) -> None:
        self.display.logger.info("Cleaning up ldap")
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                self.display.logger.warning("Can't close ldap connection")

    def init_connect(self) -> None:
        if self.scheme is not LdapScheme.AUTO:
            self.connection = ldap.LDAPConnection(
                f"{self.scheme}://{self.dc_values.host}",
                self.dc_values.base_dn,
                self.dc_values.ip,
            )
            try:
                self.__ldap_login()
            except Exception as e:
                errmsg = f"Can't login to {self.scheme} : {e}"
                raise HandledError(errmsg) from e
        else:
            self.scheme = LdapScheme.LDAP
            self.connection = ldap.LDAPConnection(
                f"{self.scheme}://{self.dc_values.host}",
                self.dc_values.base_dn,
                self.dc_values.ip,
            )
            try:
                self.__ldap_login()
            except ldap.LDAPSessionError as e:
                if str(e).find("strongerAuthRequired") >= 0:
                    self.scheme = LdapScheme.LDAPS
                    self.connection = ldap.LDAPConnection(
                        f"{self.scheme}://{self.dc_values.host}",
                        self.dc_values.base_dn,
                        self.dc_values.ip,
                    )
                    try:
                        self.__ldap_login()
                    except Exception as e:
                        errmsg = f"Can't login to {self.scheme} : {e}"
                        raise HandledError(errmsg) from e
                else:
                    errmsg = f"Can't login to {self.scheme} : {e}"
                    raise HandledError(errmsg) from e
