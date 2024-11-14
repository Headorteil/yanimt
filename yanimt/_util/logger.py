import logging
from typing import Any

from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text

from yanimt._util.consts import OPSEC_LEVEL
from yanimt._util.exceptions import HandledError


class OpsecRichHandler(RichHandler):
    def get_level_text(self, record: logging.LogRecord) -> Text:
        level_name = record.levelname
        levelno = record.levelno
        if levelno == OPSEC_LEVEL:
            level_name = "OPSEC"
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
    handler = OpsecRichHandler(
        show_path=debug,
        rich_tracebacks=debug,
        console=console,
        omit_repeated_times=not debug,
        tracebacks_show_locals=debug,
    )
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.propagate = False

    match level:
        case 0:
            logger.setLevel(60)
        case 1:
            logger.setLevel(logging.WARNING)
        case 2:
            logger.setLevel(logging.INFO)
        case 3:
            logger.setLevel(logging.DEBUG)
        case _:
            errmsg = "Invalid logging level"
            raise HandledError(errmsg)

    return logger


def get_null_logger() -> YanimtLogger:
    logger = YanimtLogger("yanimt")
    logger.addHandler(logging.NullHandler())
    return logger
