from typing import Any

from rich.progress import Progress, SpinnerColumn, TextColumn
from textual.widgets import Static


class TitleProgress(Static):
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        super().__init__(*args, **kwargs)
        self.title = "[bold]Yanimt TUI[/bold]"
        self.progress = Progress(
            TextColumn(self.title),
            SpinnerColumn("arc"),
            TextColumn("{task.description}"),
        )
        self.progress_task = None

    def on_mount(self) -> None:
        self.update_render = self.set_interval(1 / 30, self.update_progress)

    def update_progress(self) -> None:
        if self.progress_task is not None:
            self.update(self.progress)
        else:
            self.update(self.title)

    def start_task(self, title: str) -> None:
        self.stop_task()
        self.progress_task = self.progress.add_task(title, total=None)

    def stop_task(self) -> None:
        if self.progress_task is not None:
            self.progress.remove_task(self.progress_task)
        self.progress_task = None
