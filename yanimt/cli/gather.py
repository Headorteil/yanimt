from pathlib import Path
from typing import Annotated

import typer
from rich.prompt import Prompt

from yanimt._util import complete_path, log_exceptions_decorator
from yanimt._util.types import AuthProto, DnsProto, LdapScheme
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
    auth_proto: Annotated[
        AuthProto,
        typer.Option(
            "--auth-proto",
            help="Use Kerberos or NTLM authentication. If auto, it try with NTLM then with kerberos",
            rich_help_panel="Authentication",
        ),
    ] = AuthProto.AUTO,
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
        LdapScheme,
        typer.Option(
            "--ldap-scheme",
            "-l",
            help="Ldap scheme. If auto, it try ldap then ldaps",
            rich_help_panel="Connection",
        ),
    ] = LdapScheme.AUTO,
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
        DnsProto,
        typer.Option(
            "--dns-proto",
            help="DNS protocol. If auto, it try UDP tne TCP",
            rich_help_panel="Connection",
        ),
    ] = DnsProto.AUTO,
) -> None:
    """Gather all needed information from the Active Directory."""
    logger = ctx.obj.logger
    config = ctx.obj.config

    if ask_password:
        if password is not None:
            logger.critical(
                "Can't ask for password because you already provide it in the command line"
            )
            raise typer.Exit(code=1)
        password = Prompt.ask("Password", password=True)

    log_exceptions_decorator(
        config.merge_with_args,
        ctx,
        username=username,
        password=password,
        domain=domain,
        aes_key=aes_key,
        ccache_path=ccache_path,
        auth_proto=auth_proto,
        dc_ip=dc_ip,
        dc_host=dc_host,
        ldap_scheme=ldap_scheme,
        dns_ip=dns_ip,
        dns_proto=dns_proto,
        hashes=hashes,
    )

    ctx.obj.gatherer = log_exceptions_decorator(
        YanimtGatherer,
        ctx,
        ctx.obj.config,
        console=ctx.obj.console,
        display=ctx.obj.display,
        pager=ctx.obj.pager,
        live=ctx.obj.live,
        logger=logger,
        debug=ctx.obj.debug,
        username=config.username,
        password=config.password,
        domain=config.domain,
        aes_key=config.aes_key,
        ccache_path=config.ccache_path,
        auth_proto=config.auth_proto,
        dc_ip=config.dc_ip,
        dc_host=config.dc_host,
        ldap_scheme=config.ldap_scheme,
        dns_ip=config.dns_ip,
        dns_proto=config.dns_proto,
        hashes=config.hashes,
    )


@app.command("domain-sid", help="Gather the domain sid")
def domain_sid(ctx: typer.Context) -> None:
    log_exceptions_decorator(ctx.obj.gatherer.gather_domain_sid, ctx)


@app.command("secrets", help="Gather secrets")
def secrets(ctx: typer.Context) -> None:
    log_exceptions_decorator(ctx.obj.gatherer.gather_secrets, ctx)


@app.command("users", help="Gather users")
def users(ctx: typer.Context) -> None:
    log_exceptions_decorator(ctx.obj.gatherer.gather_users, ctx)


@app.command("computers", help="Gather computers")
def computers(
    ctx: typer.Context,
    resolve: Annotated[
        bool,
        typer.Option(
            "--resolve/--no-resolve",
            "-r/-R",
            help="Resolve the DNS name of the machines",
        ),
    ] = True,
) -> None:
    log_exceptions_decorator(ctx.obj.gatherer.gather_computers, ctx, resolve=resolve)


@app.command("groups", help="Gather groups")
def groups(ctx: typer.Context) -> None:
    log_exceptions_decorator(ctx.obj.gatherer.gather_groups, ctx)


@app.command("ous", help="Gather organisational units")
def organisational_units(ctx: typer.Context) -> None:
    log_exceptions_decorator(ctx.obj.gatherer.gather_organisational_units, ctx)


@app.command("all", help="Gather all required data from AD")
def all_(ctx: typer.Context) -> None:
    log_exceptions_decorator(ctx.obj.gatherer.gather_all, ctx)
