from textual.app import ComposeResult
from textual.widgets import DataTable, Footer, Markdown

from yanimt._tui.tabs import YanimtObjectScreen, YanimtTable


class UserTable(YanimtTable):
    def on_mount(self) -> None:
        for key, label in (
            ("sam_account_name", "Sam account name"),
            ("uas", "UAC"),
            ("password_last_set", "Password last set"),
            ("nt_hash", "NT hash"),
            ("lm_hash", "LM hash"),
            ("last_logon_timestamp", "Last logon timestamp"),
        ):
            self.add_column(label, key=key)
        self.render_users()

    def render_users(self) -> None:
        self.clear()
        for user in self.database.get_users():
            self.add_row(
                user.rich(),
                user.user_account_control,
                user.pwd_last_set,
                user.nt_hash,
                user.lm_hash,
                user.last_logon_timestamp,
                key=user.sid,
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
        user = self.database.get_user(message.cell_key.row_key.value)  # pyright: ignore [reportArgumentType]
        self.app.push_screen(UserScreen(user))


class UserScreen(YanimtObjectScreen):
    """User specific screen."""

    def compose(self) -> ComposeResult:
        md = f"# {self.obj.sam_account_name}\n- "
        md += "\n- ".join(
            "**{}**: {}".format(*item)
            for item in vars(self.obj).items()
            if not (item[0].startswith("_") or item[0] in ("computer_id", "computer"))
        )
        yield Footer()
        yield Markdown(markdown=md, id="obj_widget")
