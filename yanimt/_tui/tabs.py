from typing import Any, ClassVar

from textual.binding import BindingType
from textual.screen import ModalScreen
from textual.widgets import DataTable


class YanimtTable(DataTable[Any]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        super().__init__(*args, **kwargs)
        self.database = self.app.database  # pyright: ignore [reportAttributeAccessIssue]
        self.current_sorts = set()
        self.zebra_stripes = True
        self.fixed_columns = 1

    def sort_reverse(self, sort_type: str) -> bool:
        """Determine if `sort_type` is ascending or descending."""
        reverse = sort_type in self.current_sorts
        if reverse:
            self.current_sorts.remove(sort_type)
        else:
            self.current_sorts.add(sort_type)
        return reverse


class YanimtObjectScreen(ModalScreen[Any]):
    BINDINGS: ClassVar[list[BindingType]] = [
        ("escape", "escape", "Escape"),
        ("up", "up", ""),
        ("down", "down", ""),
    ]

    def __init__(self, obj: Any, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        super().__init__(*args, **kwargs)
        self.obj = obj

    def action_up(self) -> None:
        self.get_widget_by_id("obj_widget").scroll_up()

    def action_down(self) -> None:
        self.get_widget_by_id("obj_widget").scroll_down()

    def action_escape(self) -> None:
        self.app.pop_screen()
