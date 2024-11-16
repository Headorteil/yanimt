import logging
from logging import LogRecord
from typing import Any

from rich._null_file import NullFile
from textual.widgets import RichLog

from yanimt._util.logger import OpsecRichHandler, YanimtLogger


class TuiRichHandler(OpsecRichHandler):
    def __init__(self, log_widget: RichLog, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        super().__init__(*args, **kwargs)
        self.log_widget = log_widget

    def emit(self, record: LogRecord) -> None:
        message = self.format(record)

        message_renderable = self.render_message(record, message)
        log_renderable = self.render(
            record=record, traceback=None, message_renderable=message_renderable
        )
        if isinstance(self.console.file, NullFile):
            self.handleError(record)
        else:
            try:
                log_renderable.expand = False  # pyright: ignore [reportAttributeAccessIssue]
                self.log_widget.write(log_renderable)
            except Exception:
                self.handleError(record)


def get_tui_logger(log_widget: RichLog) -> YanimtLogger:
    logger = YanimtLogger("yanimt")
    handler = TuiRichHandler(
        log_widget,
        show_path=False,
    )
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.propagate = False
    logger.setLevel(logging.DEBUG)

    return logger
