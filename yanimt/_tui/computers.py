from textual.app import ComposeResult
from textual.widgets import DataTable, Footer, Markdown

from yanimt._tui.tabs import YanimtObjectScreen, YanimtTable


class ComputerTable(YanimtTable):
    def on_mount(self) -> None:
        for key, label in (
            ("fqdn", "Full quialified domain name"),
            ("ip", "IP"),
            ("status", "Status"),
            ("sam_account_name", "Sam account name"),
            ("uas", "UAC"),
            ("password_last_set", "Password last set"),
            ("nt_hash", "NT hash"),
            ("lm_hash", "LM hash"),
            ("last_logon_timestamp", "Last logon timestamp"),
        ):
            self.add_column(label, key=key)
        self.render_computers()

    def render_computers(self) -> None:
        self.clear()
        for computer in self.database.get_computers():
            self.add_row(
                computer.rich(),
                computer.ip,
                computer.status,
                computer.user.sam_account_name,
                computer.user.user_account_control,
                computer.user.pwd_last_set,
                computer.user.nt_hash,
                computer.user.lm_hash,
                computer.user.last_logon_timestamp,
                key=computer.fqdn,
            )

    def on_data_table_header_selected(self, message: DataTable.HeaderSelected) -> None:
        key = message.column_key.value

        match key:
            case "sam_account_name":

                def key_function(key: str | None) -> str:  # pyright: ignore [reportRedeclaration]
                    return "" if key is None else key.lower()
            case _:

                def key_function(key: str | None) -> str:
                    return "" if key is None else str(key)

        self.sort(
            key,  # pyright: ignore [reportArgumentType]
            key=key_function,
            reverse=self.sort_reverse(key),  # pyright: ignore [reportArgumentType]
        )

    def on_data_table_cell_selected(self, message: DataTable.CellSelected) -> None:
        computer = self.database.get_computer(message.cell_key.row_key.value)  # pyright: ignore [reportArgumentType]
        self.app.push_screen(ComputerScreen(computer))


class ComputerScreen(YanimtObjectScreen):
    """Computer specific screen."""

    def compose(self) -> ComposeResult:
        md = f"# {self.obj.fqdn}\n- "
        md += "\n- ".join(
            "**{}**: {}".format(*item)
            for item in vars(self.obj).items()
            if not (item[0].startswith("_") or item[0] == "user")
        )
        md += "\n- ".join(
            "**{}**: {}".format(*item)
            for item in vars(self.obj.user).items()
            if not item[0].startswith("_")
        )
        yield Footer()
        yield Markdown(markdown=md, id="obj_widget")
