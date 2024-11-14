from datetime import UTC, datetime
from typing import Any

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


def complete_path() -> (
    list[None]
):  # Typer bug : https://github.com/fastapi/typer/issues/951
    return []
