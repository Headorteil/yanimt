import os
from collections.abc import Iterator
from pathlib import Path

from dns.name import from_text as dns_name_from_text
from dns.name import root as root_dns_name
from dns.resolver import LifetimeTimeout, Resolver
from impacket.krb5.ccache import CCache
from impacket.smbconnection import SessionError, SMBConnection

from yanimt._util.consts import SMB_TIMEOUT
from yanimt._util.exceptions import HandledError, TimeOutError
from yanimt._util.types import AuthProto, Display, DnsProto


class ADAuthentication:
    def __init__(
        self,
        display: Display,
        auth_proto: AuthProto,
        username: str | None,
        password: str | None,
        hashes: str | None,
        aes_key: str | None,
        ccache_path: Path | None,
        domain: str | None,
    ) -> None:
        self.user_domain = domain
        use_ccache = ccache_path is not None
        len_provided_creds = sum(
            1 for i in (password, hashes, aes_key, ccache_path) if i is not None
        )
        if auth_proto is AuthProto.KERBEROS:
            self.auth_proto = AuthProto.KERBEROS
            if len_provided_creds > 1:
                errmsg = "More than one secret was provided"
                raise HandledError(errmsg)
            if len_provided_creds == 0:
                use_ccache = True
        elif auth_proto is AuthProto.NTLM:
            self.auth_proto = AuthProto.NTLM
            if len_provided_creds != 1:
                errmsg = "You must provide one secret"
                raise HandledError(errmsg)
            if aes_key is not None:
                errmsg = "AES Key cannot be used with NTLM authentification"
                raise HandledError(errmsg)
            if ccache_path is not None:
                errmsg = "CCache cannot be used with NTLM authentification"
                raise HandledError(errmsg)
        else:
            if len_provided_creds > 1:
                errmsg = "More than one secret was provided"
                raise HandledError(errmsg)
            if len_provided_creds == 0:
                self.auth_proto = AuthProto.KERBEROS
                use_ccache = True
            elif (aes_key is not None) or (ccache_path is not None):
                self.auth_proto = AuthProto.KERBEROS
            else:
                self.auth_proto = AuthProto.AUTO

        self.username = username if username is not None else ""
        self.password = password if password is not None else ""
        self.aes_key = aes_key if aes_key is not None else ""
        self.lm_hash = ""
        self.nt_hash = ""
        self.tgt = None
        self.ccache = None
        if hashes is not None:
            if ":" in hashes:
                display.logger.debug("Hash argument -> LM:NT")
                self.lm_hash, self.nt_hash = hashes.split(":")
            else:
                display.logger.debug("Hash argument -> NT Only")
                self.nt_hash = hashes

        if use_ccache:
            if ccache_path is None:
                if ("KRB5CCNAME" not in os.environ) or (not os.environ["KRB5CCNAME"]):
                    errmsg = "Env var KRB5CCNAME not found"
                    raise HandledError(errmsg)
                ccache_path = Path(os.environ["KRB5CCNAME"])
            self.ensure_file_readable(ccache_path)
            self.ccache = CCache.loadFile(ccache_path)
            self.parse_ccache()

        if self.username == "":
            errmsg = "Username is empty"
            raise HandledError(errmsg)

        display.logger.debug(
            "Authentification configuration -> Domain : %s | Username : %s | Password : %s | Aes Key : %s | LM Hash : %s | NT Hash : %s | TGT : %s",
            self.user_domain,
            self.username,
            self.password,
            self.aes_key,
            self.lm_hash,
            self.nt_hash,
            self.tgt is not None,
        )

    @staticmethod
    def ensure_file_readable(path: Path) -> None:
        if not path.is_file():
            errmsg = f"{path} don't exist"
            raise HandledError(errmsg)
        try:
            with path.open("rb"):
                pass
        except PermissionError as e:
            errmsg = f"{path} is not readable"
            raise HandledError(errmsg) from e

    def parse_ccache(self) -> None:
        if self.ccache is None:
            errmsg = "Ccache is empty"
            raise HandledError(errmsg)

        if self.user_domain is None:
            if self.ccache.principal is None:
                errmsg = "No valid credentials found in cache"
                raise HandledError(errmsg)
            if self.ccache.principal.realm is None:
                errmsg = "No valid credentials found in cache"
                raise HandledError(errmsg)
            self.user_domain = self.ccache.principal.realm["data"].decode("utf-8")

        principal = f"krbtgt/{self.user_domain.upper()}@{self.user_domain.upper()}"
        creds = self.ccache.getCredential(principal)
        if creds is not None:
            self.tgt = creds.toTGT()
        else:
            errmsg = "No valid credentials found in cache"
            raise HandledError(errmsg)

        if self.username == "":
            self.username = creds["client"].prettyPrint().split(b"@")[0].decode("utf-8")


class DCValues:
    def __init__(
        self,
        display: Display,
        domain: str | None,
        host: str | None,
        ip: str | None,
        dns_ip: str | None,
        dns_proto: DnsProto,
    ) -> None:
        self.__display = display
        self.dns_proto = dns_proto

        self.resolver = Resolver()
        self.resolver.use_search_by_default = True
        if dns_ip:
            self.resolver.nameservers = [dns_ip]

        if ip and ((not host) or (not domain)):
            self.ip = ip
            retrieved_server_name, retrieved_domain_name = (
                self.__get_machine_name_domain(ip)
            )
            if domain:
                self.domain = domain
            else:
                self.domain = retrieved_domain_name
            if host:
                self.host = host
            else:
                self.host = f"{retrieved_server_name}.{self.domain}"
        elif host and ((not domain) or (not ip)):
            self.host = host
            if ip:
                self.ip = ip
            else:
                self.dns_proto, addresses = resolve_dns(
                    self.__display, self.resolver, self.dns_proto, host
                )
                self.ip = next(addresses)
            if domain:
                self.domain = domain
            else:
                _, self.domain = self.__get_machine_name_domain(self.ip)
        elif domain and ((not host) or (not ip)):
            self.domain = domain
            retrieved_server_name = None
            if ip:
                self.ip = ip
            else:
                self.dns_proto, addresses = resolve_dns(
                    self.__display, self.resolver, self.dns_proto, self.domain
                )
                for address in addresses:
                    try:
                        retrieved_server_name, _ = self.__get_machine_name_domain(
                            address
                        )
                    except TimeOutError:
                        self.__display.logger.warning(
                            "Can't join DC -> IP : %s", address
                        )
                        continue
                    self.ip = address
                    break
                else:
                    errmsg = "Can't find a responding DC"
                    raise HandledError(errmsg)

            if host:
                self.host = host
            else:
                if retrieved_server_name is None:
                    retrieved_server_name, _ = self.__get_machine_name_domain(self.ip)
                self.host = f"{retrieved_server_name}.{self.domain}"
        else:
            domain_name = self.resolver.domain
            if domain_name == root_dns_name:
                errmsg = "Can't find domain with DNS config"
                raise HandledError(errmsg)
            self.domain = domain_name.to_text(omit_final_dot=True)
            self.dns_proto, addresses = resolve_dns(
                self.__display, self.resolver, self.dns_proto, self.domain
            )
            for address in addresses:
                try:
                    retrieved_server_name, _ = self.__get_machine_name_domain(address)
                except TimeOutError:
                    self.__display.logger.warning("Can't join DC -> IP : %s", address)
                    continue
                self.ip = address
                break
            else:
                errmsg = "Can't find a responding DC"
                raise HandledError(errmsg)
            self.host = f"{retrieved_server_name}.{self.domain}"

        self.domain = self.domain.lower()
        self.host = self.host.lower()

        domain_parts = self.domain.split(".")
        base_dn = ""
        for i in domain_parts:
            base_dn += f"dc={i},"
        self.base_dn = base_dn[:-1]

        if not dns_ip:
            self.resolver.nameservers = [self.ip]

        self.resolver.domain = dns_name_from_text(self.domain)

        self.__display.logger.debug(
            "Connextion configuration -> Domain : %s | Host : %s | IP : %s | DNS : %s://%s",
            self.domain,
            self.host,
            self.ip,
            self.dns_proto.value,
            self.resolver.nameservers,
        )

    def __get_machine_name_domain(self, ip: str) -> tuple[str, str]:
        self.__display.logger.opsec("[SMB -> %s] Finding machine name via smb", ip)
        s = None
        try:
            s = SMBConnection(ip, ip, timeout=SMB_TIMEOUT)
            s.login("", "")
        except OSError as e:
            if str(e).find("timed out") > 0:
                errmsg = "Timed out"
                raise TimeOutError(errmsg) from e
            raise
        except SessionError as e:
            if str(e).find("STATUS_NOT_SUPPORTED") > 0:
                errmsg = "The SMB request is not supported, NTLM is probably disabled"
                raise HandledError(errmsg) from e
            raise
        except Exception as e:
            if s is None or s.getServerName() == "":
                errmsg = "Error while anonymous logging into DC"
                raise HandledError(errmsg) from e
        s.logoff()
        domain = s.getServerDNSDomainName()
        server_name = s.getServerName()
        return server_name, domain


def resolve_dns(
    display: Display, resolver: Resolver, dns_proto: DnsProto, host: str
) -> tuple[DnsProto, Iterator[str]]:
    if dns_proto is DnsProto.UDP:
        display.logger.opsec(
            "[DNS (UDP) -> %s] Resolving host -> %s", host, resolver.nameservers
        )
        try:
            return (DnsProto.UDP, resolver.resolve_name(host, tcp=False).addresses())
        except Exception as e:
            errmsg = "Can't resolve dc host"
            raise HandledError(errmsg) from e
    if dns_proto is DnsProto.TCP:
        display.logger.opsec(
            "[DNS (TCP) -> %s] Resolving host -> %s", host, resolver.nameservers
        )
        try:
            return (DnsProto.TCP, resolver.resolve_name(host, tcp=True).addresses())
        except Exception as e:
            errmsg = "Can't resolve dc host"
            raise HandledError(errmsg) from e
    else:
        display.logger.opsec(
            "[DNS (UDP) -> %s] Resolving host -> %s", host, resolver.nameservers
        )
        try:
            return (DnsProto.UDP, resolver.resolve_name(host, tcp=False).addresses())
        except LifetimeTimeout:
            display.logger.debug("Failed resolving via UDP, resolving host via TCP")
            display.logger.opsec(
                "[DNS (TCP) -> %s] Resolving host -> %s", host, resolver.nameservers
            )
            try:
                return (DnsProto.TCP, resolver.resolve_name(host, tcp=True).addresses())
            except Exception as e:
                errmsg = "Can't resolve dc host"
                raise HandledError(errmsg) from e
        except Exception as e:
            errmsg = "Can't resolve dc host"
            raise HandledError(errmsg) from e
