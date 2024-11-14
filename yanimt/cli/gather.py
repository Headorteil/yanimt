from pathlib import Path
from typing import Annotated

import typer
from rich.prompt import Prompt

from yanimt._util import complete_path
from yanimt._util.exceptions import HandledError
from yanimt._util.types import DnsProto, LdapScheme
from yanimt.gatherer import YanimtGatherer

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})


@app.callback(help="Gather required data from AD to a local file")
def main(
    ctx: typer.Context,
    username: Annotated[
        str | None,
        typer.Option(
            "--username",
            "-u",
            help="Username to connect with",
            show_default=False,
            rich_help_panel="Authentication",
        ),
    ] = None,
    password: Annotated[
        str | None,
        typer.Option(
            "--password",
            "-p",
            help="Password to connect with",
            show_default=False,
            rich_help_panel="Authentication",
        ),
    ] = None,
    ask_password: Annotated[
        bool,
        typer.Option(
            "--ask-password",
            "-P",
            help="Ask for a password",
            rich_help_panel="Authentication",
        ),
    ] = False,
    hashes: Annotated[
        str | None,
        typer.Option(
            "--hashes",
            "-H",
            help="NTLM hashes, format is LMHASH:NTHASH",
            show_default=False,
            rich_help_panel="Authentication",
        ),
    ] = None,
    kerberos: Annotated[
        bool | None,
        typer.Option(
            "--kerberos/--no-kerberos",
            "-k/-K",
            show_default=False,
            help="Use kerberos authentication. If ommited, it try with NTLM then with kerberos",
            rich_help_panel="Authentication",
        ),
    ] = None,
    aes_key: Annotated[
        str | None,
        typer.Option(
            "--aes-key",
            "-a",
            help="AES key to use for Kerberos Authentication (128 or 256 bits)",
            show_default=False,
            rich_help_panel="Authentication",
        ),
    ] = None,
    ccache_path: Annotated[
        Path | None,
        typer.Option(
            "--ccache-path",
            "-c",
            exists=True,
            file_okay=True,
            readable=True,
            resolve_path=True,
            help="Path of the ccache. If ommited and no other authentification method is supplied, it checks KRB5CCNAME env var",
            show_default=False,
            autocompletion=complete_path,
            rich_help_panel="Authentication",
        ),
    ] = None,
    domain: Annotated[
        str | None,
        typer.Option(
            "--domain",
            "-d",
            help="Domain to query. If ommited, it checks --dc-ip, --dh-host or resolv.conf",
            show_default=False,
            rich_help_panel="Connection",
        ),
    ] = None,
    dc_ip: Annotated[
        str | None,
        typer.Option(
            "--dc-ip",
            "-i",
            help="IP address of the domain controller. If ommited it checks the --dc-host, --domain",
            show_default=False,
            rich_help_panel="Connection",
        ),
    ] = None,
    dc_host: Annotated[
        str | None,
        typer.Option(
            "--dc-host",
            help="Hostname of the domain controller. If ommited it checks the --dc-ip or --domain",
            show_default=False,
            rich_help_panel="Connection",
        ),
    ] = None,
    ldap_scheme: Annotated[
        LdapScheme | None,
        typer.Option(
            "--ldap-scheme",
            "-l",
            help="Ldap scheme. If ommited, it try ldap then ldaps",
            show_default=False,
            rich_help_panel="Connection",
        ),
    ] = None,
    dns_ip: Annotated[
        str | None,
        typer.Option(
            "--dns-ip",
            "-D",
            help="DNS IP. If ommited, it try with DC IP",
            show_default=False,
            rich_help_panel="Connection",
        ),
    ] = None,
    dns_proto: Annotated[
        DnsProto | None,
        typer.Option(
            "--dns-proto",
            help="DNS protocol. If ommited, it try UDP tne TCP",
            show_default=False,
            rich_help_panel="Connection",
        ),
    ] = None,
) -> None:
    """Gather all needed information from the Active Directory."""
    logger = ctx.obj.logger

    if ctx.obj.debug:
        ctx.obj.no_stacktrace_exceptions = ()
        ctx.obj.stacktrace_exceptions = BaseException
    else:
        ctx.obj.no_stacktrace_exceptions = HandledError
        ctx.obj.stacktrace_exceptions = Exception

    if ask_password:
        if password is not None:
            logger.critical(
                "Can't ask for password because you already provide it in the command line"
            )
            raise typer.Exit(code=1)
        password = Prompt.ask("Password", password=True)

    try:
        ctx.obj.gatherer = YanimtGatherer(
            ctx.obj.config,
            console=ctx.obj.console,
            pager=ctx.obj.pager,
            live=ctx.obj.live,
            logger=logger,
            debug=ctx.obj.debug,
            username=username,
            password=password,
            domain=domain,
            aes_key=aes_key,
            ccache_path=ccache_path,
            kerberos=kerberos,
            dc_ip=dc_ip,
            dc_host=dc_host,
            ldap_scheme=ldap_scheme,
            dns_ip=dns_ip,
            dns_proto=dns_proto,
            hashes=hashes,
        )
    except ctx.obj.no_stacktrace_exceptions as e:
        logger.critical(e)
        raise typer.Exit(code=1) from e
    except ctx.obj.stacktrace_exceptions as e:
        logger.exception("Unhandled error")
        raise typer.Exit(code=2) from e


@app.command("all", help="Gather all required data from AD")
def all_(ctx: typer.Context) -> None:
    logger = ctx.obj.logger

    try:
        ctx.obj.gatherer.all_()
    except ctx.obj.no_stacktrace_exceptions as e:
        logger.critical(e)
        raise typer.Exit(code=1) from e
    except ctx.obj.stacktrace_exceptions as e:
        logger.exception("Unhandled error")
        raise typer.Exit(code=2) from e