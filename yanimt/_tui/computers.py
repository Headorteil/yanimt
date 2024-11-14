from textual.app import ComposeResult
from textual.widgets import DataTable, Footer, Markdown

from yanimt._tui.tabs import YanimtObjectScreen, YanimtTable


class ComputerTable(YanimtTable):
    def on_mount(self) -> None:
        for key, label in (
            ("fqdn", "Full quialified domain name"),
            ("ip", "IP"),
            ("status", "Status"),
        ):
            self.add_column(label, key=key)
        for computer in self.database.get_computers():
            self.add_row(
                computer.fqdn,
                computer.ip,
                computer.status,
                key=computer.fqdn,
            )

    def on_data_table_header_selected(self, message: DataTable.HeaderSelected) -> None:
        key = message.column_key.value

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
            if not item[0].startswith("_")
        )
        yield Footer()
        yield Markdown(markdown=md, id="obj_widget")
