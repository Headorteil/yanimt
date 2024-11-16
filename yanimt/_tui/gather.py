from pathlib import Path
from typing import Any, ClassVar

from textual.app import ComposeResult
from textual.binding import BindingType
from textual.containers import Center, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Input,
    Label,
    RadioButton,
    RadioSet,
    Rule,
)

from yanimt._util.types import AuthProto, DnsProto, LdapScheme
from yanimt.gatherer import YanimtGatherer


class InitGatherScreen(ModalScreen[Any]):
    BINDINGS: ClassVar[list[BindingType]] = [
        ("escape", "escape", "Escape"),
    ]

    def action_escape(self) -> None:
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        config = self.app.config  # pyright: ignore [reportAttributeAccessIssue]

        yield Footer()
        yield VerticalScroll(
            Label("Authentication", classes="category"),
            Label("Username", classes="question"),
            Input(
                placeholder="headorteil",
                id="username",
                value=config.username,
            ),
            Label("Password", classes="question"),
            Input(
                placeholder="mypasswordistrong",
                id="password",
                value=config.password,
            ),
            Label("Hashes", classes="question"),
            Input(
                placeholder="bb88309b03e9c575096ea69bcd90fda9",
                id="hashes",
                value=config.hashes,
            ),
            Label("Authentication protocol", classes="question"),
            Center(
                RadioSet(
                    RadioButton(
                        "Auto",
                        name=AuthProto.AUTO,
                        value=config.auth_proto is AuthProto.AUTO,
                    ),
                    RadioButton(
                        "Kerberos",
                        name=AuthProto.KERBEROS,
                        value=config.auth_proto is AuthProto.KERBEROS,
                    ),
                    RadioButton(
                        "NTLM",
                        name=AuthProto.NTLM,
                        value=config.auth_proto is AuthProto.NTLM,
                    ),
                    id="auth_proto",
                ),
            ),
            Label("Aes key", classes="question"),
            Input(
                placeholder="AAAA==",
                id="aes_key",
                value=config.aes_key,
            ),
            Label("Ccache path", classes="question"),
            Input(
                placeholder="/path/to/my/file.ccache",
                id="ccache_path",
                value=None if config.ccache_path is None else config.ccache_path,
            ),
            Label("Connection", classes="category"),
            Label("Domain", classes="question"),
            Input(
                placeholder="super.lab",
                id="domain",
                value=config.domain,
            ),
            Label("Dc ip", classes="question"),
            Input(
                placeholder="10.0.0.1",
                id="dc_ip",
                value=config.dc_ip,
            ),
            Label("Dc host", classes="question"),
            Input(
                placeholder="dc.super.lab",
                id="dc_host",
                value=config.dc_host,
            ),
            Label("Ldap scheme", classes="question"),
            Center(
                RadioSet(
                    RadioButton(
                        "Auto",
                        name=LdapScheme.AUTO,
                        value=config.ldap_scheme is LdapScheme.AUTO,
                    ),
                    RadioButton(
                        "LDAP",
                        name=LdapScheme.LDAP,
                        value=config.ldap_scheme is LdapScheme.LDAP,
                    ),
                    RadioButton(
                        "LDAPS",
                        name=LdapScheme.LDAPS,
                        value=config.ldap_scheme is LdapScheme.LDAPS,
                    ),
                    id="ldap_scheme",
                ),
            ),
            Label("Dns ip", classes="question"),
            Input(
                placeholder="10.0.0.1",
                id="dns_ip",
                value=config.dns_ip,
            ),
            Label("Dns proto", classes="question"),
            Center(
                RadioSet(
                    RadioButton(
                        "Auto",
                        name=DnsProto.AUTO,
                        value=config.dns_proto is DnsProto.AUTO,
                    ),
                    RadioButton(
                        "TCP", name=DnsProto.TCP, value=config.dns_proto is DnsProto.TCP
                    ),
                    RadioButton(
                        "UDP", name=DnsProto.UDP, value=config.dns_proto is DnsProto.UDP
                    ),
                    id="dns_proto",
                ),
            ),
            Center(Checkbox("Save config", id="save_config")),
            Rule(),
            Button("Submit"),
        )

    def on_button_pressed(self, message_: Button.Pressed) -> None:  # noqa: ARG002
        username = (
            None if (value := self.get_widget_by_id("username").value) == "" else value  # pyright: ignore [reportAttributeAccessIssue]
        )
        password = (
            None if (value := self.get_widget_by_id("password").value) == "" else value  # pyright: ignore [reportAttributeAccessIssue]
        )
        hashes = (
            None if (value := self.get_widget_by_id("hashes").value) == "" else value  # pyright: ignore [reportAttributeAccessIssue]
        )
        auth_proto = (
            AuthProto(self.get_widget_by_id("auth_proto").pressed_button.name)  # pyright: ignore [reportAttributeAccessIssue]
        )
        aes_key = (
            None if (value := self.get_widget_by_id("aes_key").value) == "" else value  # pyright: ignore [reportAttributeAccessIssue]
        )
        ccache_path = (
            None
            if (value := self.get_widget_by_id("ccache_path").value) == ""  # pyright: ignore [reportAttributeAccessIssue]
            else Path(value)
        )
        domain = (
            None if (value := self.get_widget_by_id("domain").value) == "" else value  # pyright: ignore [reportAttributeAccessIssue]
        )
        dc_ip = None if (value := self.get_widget_by_id("dc_ip").value) == "" else value  # pyright: ignore [reportAttributeAccessIssue]
        dc_host = (
            None if (value := self.get_widget_by_id("dc_host").value) == "" else value  # pyright: ignore [reportAttributeAccessIssue]
        )
        ldap_scheme = (
            LdapScheme(self.get_widget_by_id("ldap_scheme").pressed_button.name)  # pyright: ignore [reportAttributeAccessIssue]
        )
        dns_ip = (
            None if (value := self.get_widget_by_id("dns_ip").value) == "" else value  # pyright: ignore [reportAttributeAccessIssue]
        )
        dns_proto = (
            DnsProto(self.get_widget_by_id("dns_proto").pressed_button.name)  # pyright: ignore [reportAttributeAccessIssue]
        )

        config = self.app.config  # pyright: ignore [reportAttributeAccessIssue]
        config.merge_with_args(
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

        try:
            gatherer = YanimtGatherer(
                config,
                logger=self.app.logger,  # pyright: ignore [reportAttributeAccessIssue]
                live=False,
                username=config.username,
                password=config.password,
                hashes=config.hashes,
                auth_proto=config.auth_proto,
                aes_key=config.aes_key,
                ccache_path=config.ccache_path,
                domain=config.domain,
                dc_ip=config.dc_ip,
                dc_host=config.dc_host,
                ldap_scheme=config.ldap_scheme,
                dns_ip=config.dns_ip,
                dns_proto=config.dns_proto,
            )
        except Exception as e:
            self.app.logger.exception("Unhandled exception")  # pyright: ignore [reportAttributeAccessIssue]
            self.app.notify(str(e), title="Error", severity="error")
        else:
            if self.get_widget_by_id("save_config").value:  # pyright: ignore [reportAttributeAccessIssue]
                config.save()

            self.app.notify(
                "Gatherer successfully instanciated",
                title="Success",
                severity="information",
            )
            self.app.gatherer = gatherer  # pyright: ignore [reportAttributeAccessIssue]
            self.dismiss()
