from typing import Any

from rich.progress import Progress, SpinnerColumn, TextColumn
from textual.widgets import Static

from yanimt._util.consts import PROGRESS_WIDGETS


class TitleProgress(Static):
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        super().__init__(*args, **kwargs)
        self.title = "[bold]Yanimt TUI[/bold]"
        self.progress = Progress(
            TextColumn(self.title),
            SpinnerColumn("arc"),
            TextColumn("{task.description}"),
        )

    def on_mount(self) -> None:
        self.update_render = self.set_interval(1 / 30, self.update_progress)

    def update_progress(self) -> None:
        if len(self.progress.task_ids) > 0:
            self.update(self.progress)
        else:
            self.update(self.title)

    def start_task(self, title: str) -> None:
        self.stop_task()
        self.progress.add_task(title)

    def stop_task(self) -> None:
        for task_id in self.progress.task_ids:
            self.progress.remove_task(task_id)


class FooterProgress(Static):
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        super().__init__(*args, **kwargs)
        self.progress = Progress(
            *PROGRESS_WIDGETS,
        )

    def on_mount(self) -> None:
        self.update_render = self.set_interval(1 / 30, self.update_progress)

    def update_progress(self) -> None:
        if len(self.progress.task_ids) > 0:
            self.update(self.progress)
        else:
            self.update("")
