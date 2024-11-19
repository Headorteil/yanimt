from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import typer

from yanimt._util.consts import WINDOWS_MAX_TIME
from yanimt._util.types import UacCodes


def parse_windows_time(time: int) -> datetime:
    if time == WINDOWS_MAX_TIME:
        return datetime.max
    return datetime.fromtimestamp((time / 10**7) - 11644473600, tz=UTC)


def parse_uac(uac: int) -> list[UacCodes]:
    return [UacCodes(2**p) for p, v in enumerate(bin(uac)[:1:-1]) if int(v)]


def auto_str(cls: Any) -> Any:  # noqa: ANN401
    def __str__(self: Any) -> str:  # noqa: N807, ANN401
        return "{class_name}(\n    {attributes}\n)".format(
            class_name=type(self).__name__,
            attributes="\n    ".join(
                "{}={}".format(*item)
                for item in vars(self).items()
                if not item[0].startswith("_")
            ),
        )

    cls.__str__ = __str__
    return cls


# Typer bug : https://github.com/fastapi/typer/issues/951
def complete_path() -> list[None]:
    return []


def log_exceptions_decorator(
    func: Callable[[Any], Any],
    ctx: typer.Context,
    *args: Any,  # noqa: ANN401
    **kwargs: Any,  # noqa: ANN401
) -> Any:  # noqa: ANN401
    logger = ctx.obj.logger
    try:
        return func(*args, **kwargs)
    except ctx.obj.no_stacktrace_exceptions as e:
        logger.critical(e)
        raise typer.Exit(code=1) from e
    except ctx.obj.stacktrace_exceptions as e:
        logger.exception("Unhandled error")
        raise typer.Exit(code=2) from e
