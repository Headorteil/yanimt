import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text

from yanimt._util.consts import OPSEC_LEVEL
from yanimt._util.exceptions import HandledError

logging.addLevelName(OPSEC_LEVEL, "OPSEC")


class OpsecRichHandler(RichHandler):
    def get_level_text(self, record: logging.LogRecord) -> Text:
        level_name = record.levelname
        level_text = Text.styled(
            level_name.ljust(8), f"logging.level.{level_name.lower()}"
        )
        if level_name == "OPSEC":
            level_text.style = "purple"
        return level_text


class YanimtLogger(logging.Logger):
    def opsec(self, msg: Any, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        self.log(OPSEC_LEVEL, msg, *args, **kwargs)


def get_logger(console: Console, level: int, debug: bool) -> YanimtLogger:
    logger = YanimtLogger("yanimt")
    logger.setLevel(logging.DEBUG)
    handler = OpsecRichHandler(
        show_path=debug,
        rich_tracebacks=debug,
        console=console,
        omit_repeated_times=not debug,
        tracebacks_show_locals=debug,
    )
    logger.addHandler(handler)
    logger.propagate = False

    match level:
        case 0:
            handler.setLevel(60)
        case 1:
            handler.setLevel(logging.WARNING)
        case 2:
            handler.setLevel(logging.INFO)
        case 3:
            handler.setLevel(logging.DEBUG)
        case _:
            errmsg = "Invalid logging level"
            raise HandledError(errmsg)

    return logger


def add_file_handler(logger: YanimtLogger, file: Path) -> None:
    file_handler = RotatingFileHandler(file, "a", 1000000, 10)
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter("{asctime:<23} {levelname:<8} {message}", style="{")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def get_null_logger() -> YanimtLogger:
    logger = YanimtLogger("yanimt")
    logger.addHandler(logging.NullHandler())
    return logger
