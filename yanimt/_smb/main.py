from typing import Self

from impacket.examples.secretsdump import (  # pyright: ignore [reportMissingTypeStubs]
    RemoteOperations,
)
from impacket.smbconnection import SMBConnection
from rich.panel import Panel
from rich.text import Text

from yanimt._database.manager import DatabaseManager
from yanimt._database.models import Domain
from yanimt._util.consts import SMB_TIMEOUT, TABLE_STYLE
from yanimt._util.exceptions import HandledError
from yanimt._util.smart_class import ADAuthentication, DCValues
from yanimt._util.types import AuthProto, Display, SmbState


class Smb:
    def __init__(
        self,
        display: Display,
        database: DatabaseManager,
        dc_values: DCValues,
        ad_authentication: ADAuthentication,
        state: SmbState = SmbState.CONNECT,
    ) -> None:
        self.display = display
        self.database = database
        self.dc_values = dc_values
        self.ad_authentication = ad_authentication
        self.state = state

        self.connection = None
        self.domain_sid = None
        self.remote_ops = None

    def __enter__(self) -> Self:
        if self.state == SmbState.CONNECT and self.connection is None:
            self.init_connect()
        elif self.state == SmbState.REMOTEOPS and self.remote_ops is None:
            self.init_remote_ops()
        return self

    def __exit__(self, *_: object) -> None:
        self.cleanup()

    def cleanup(self) -> None:
        self.display.logger.info("Cleaning up smb")
        if self.remote_ops:
            try:
                self.remote_ops.finish()
            except Exception as e:
                self.display.logger.warning("Can't shutdown remote ops -> %s", e)

    def init_connect(self) -> None:
        connection = SMBConnection(
            self.dc_values.host, self.dc_values.ip, timeout=SMB_TIMEOUT
        )
        if self.ad_authentication.auth_proto is AuthProto.KERBEROS:
            self.display.logger.opsec(
                "[SMB (KERBEROS) -> %s] Authenticate to SMB with Kerberos",
                self.dc_values.ip,
            )
            try:
                connection.kerberosLogin(
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
            except Exception as e:
                errmsg = f"Can't login to SMB : {e}"
                raise HandledError(errmsg) from e
        elif self.ad_authentication.auth_proto is AuthProto.NTLM:
            self.display.logger.opsec(
                "[SMB (NTLM) -> %s] Authenticate to SMB with NTLM", self.dc_values.ip
            )
            try:
                connection.login(
                    self.ad_authentication.username,
                    self.ad_authentication.password,
                    domain=self.dc_values.domain,
                    lmhash=self.ad_authentication.lm_hash,
                    nthash=self.ad_authentication.nt_hash,
                )
            except Exception as e:
                errmsg = f"Can't login to SMB : {e}"
                raise HandledError(errmsg) from e
        else:
            self.ad_authentication.auth_proto = AuthProto.NTLM
            self.display.logger.opsec(
                "[SMB (NTLM) -> %s] Authenticate to SMB with NTLM", self.dc_values.ip
            )
            try:
                connection.login(
                    self.ad_authentication.username,
                    self.ad_authentication.password,
                    domain=self.dc_values.domain,
                    lmhash=self.ad_authentication.lm_hash,
                    nthash=self.ad_authentication.nt_hash,
                )
            except Exception:
                self.ad_authentication.auth_proto = AuthProto.KERBEROS
                self.display.logger.debug(
                    "Authenticate to SMB with NTLM failed, tying Kerberos"
                )
                self.display.logger.opsec(
                    "[SMB (KERBEROS) -> %s] Authenticate to SMB with Kerberos",
                    self.dc_values.ip,
                )
                try:
                    connection.kerberosLogin(
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
                except Exception as e:
                    errmsg = f"Can't login to SMB : {e}"
                    raise HandledError(errmsg) from e
        self.connection = connection

    def init_remote_ops(self) -> None:
        if self.connection is None:
            self.init_connect()

        self.remote_ops = RemoteOperations(
            self.connection,
            self.ad_authentication.auth_proto is AuthProto.KERBEROS,
            self.dc_values.ip,
            None,
        )

    def pull_domain_sid(self) -> None:
        if self.remote_ops is None:
            self.init_remote_ops()

        self.display.logger.opsec("[SMB -> %s] Querying domain SID", self.dc_values.ip)
        domain_sid = self.remote_ops.getDomainSid()  # pyright: ignore [reportOptionalMemberAccess]
        domain = Domain(sid=domain_sid)
        self.database.put_domain(domain)
        self.domain_sid = domain_sid

    def get_domain_sid(self) -> str:
        if self.domain_sid is None:
            self.pull_domain_sid()

        return self.domain_sid  # pyright: ignore [reportReturnType]

    def display_domain_sid(self) -> None:
        if self.domain_sid is None:
            self.pull_domain_sid()

        self.display.console.print(
            Panel(
                Text(self.domain_sid, style=TABLE_STYLE, justify="center"),  # pyright: ignore [reportArgumentType]
                title="Domain SID",
            )
        )
