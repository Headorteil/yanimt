from dns.resolver import LifetimeTimeout

from yanimt._database.manager import DatabaseManager
from yanimt._database.models import Computer
from yanimt._util.exceptions import HandledError
from yanimt._util.smart_class import DCValues
from yanimt._util.types import Display, DnsProto


def resolve_dns(
    display: Display,
    dc_values: DCValues,
    host: str,
    database: DatabaseManager | None = None,
) -> str | None:
    if dc_values.dns_proto is DnsProto.UDP:
        display.logger.opsec(
            "[DNS (UDP) -> %s] Resolving host -> %s",
            dc_values.resolver.nameservers,
            host,
        )
        try:
            ips = dc_values.resolver.resolve_name(host, tcp=False).addresses()
        except Exception as e:
            errmsg = "Can't resolve host"
            raise HandledError(errmsg) from e
    elif dc_values.dns_proto is DnsProto.TCP:
        display.logger.opsec(
            "[DNS (TCP) -> %s] Resolving host -> %s",
            dc_values.resolver.nameservers,
            host,
        )
        try:
            ips = dc_values.resolver.resolve_name(host, tcp=True).addresses()
        except Exception as e:
            errmsg = "Can't resolve host"
            raise HandledError(errmsg) from e
    else:
        display.logger.opsec(
            "[DNS (UDP) -> %s] Resolving host -> %s",
            dc_values.resolver.nameservers,
            host,
        )
        try:
            ips = dc_values.resolver.resolve_name(host, tcp=False).addresses()
            dc_values.dns_proto = DnsProto.UDP
        except LifetimeTimeout:
            display.logger.debug("Failed resolving via UDP, resolving host via TCP")
            display.logger.opsec(
                "[DNS (TCP) -> %s] Resolving host -> %s",
                dc_values.resolver.nameservers,
                host,
            )
            try:
                ips = dc_values.resolver.resolve_name(host, tcp=True).addresses()
                dc_values.dns_proto = DnsProto.TCP
            except Exception as e:
                errmsg = "Can't resolve host"
                raise HandledError(errmsg) from e
        except Exception as e:
            errmsg = "Can't resolve host"
            raise HandledError(errmsg) from e

    ips_list = list(ips)
    if len(ips_list) == 0:
        errmsg = "Can't resolve host"
        raise HandledError(errmsg)
    if len(ips_list) > 1:
        errmsg = "Host resolve to multiples IPs"
        raise HandledError(errmsg)
    ip = ips_list[0]

    if database is None:
        return ip

    computer = Computer(fqdn=host.lower(), ip=ip)
    database.put_computer(computer)
    return None
