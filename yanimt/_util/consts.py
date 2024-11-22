from pathlib import Path

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

PROGRESS_WIDGETS = [
    SpinnerColumn("arc"),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    MofNCompleteColumn(),
    TimeElapsedColumn(),
]

ADMIN_GROUPS_SIDS = {
    "{domain_sid}-512",
    "{domain_sid}-519",
    "S-1-5-32-544",
}

NULL_LM = "aad3b435b51404eeaad3b435b51404ee"
NULL_NT = "31d6cfe0d16ae931b73c59d7e0c089c0"
WINDOWS_MAX_TIME = 9223372036854775807


DNS_TIMEOUT = 10
SMB_TIMEOUT = 10

DEFAULT_TOOL_DIR = Path.home().resolve() / ".yanimt"
DEFAULT_CONFIG_FILE = DEFAULT_TOOL_DIR / "config.yml"
APP_PATH = Path(__file__).parent.parent
TCSS_PATH = APP_PATH / "static" / "tcss"

DEFAULT_DB_URI = f"sqlite:///{DEFAULT_TOOL_DIR}/database.sql"
DEFAULT_LOG_DIR = DEFAULT_TOOL_DIR / "logs"
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "yanimt.log"

OPSEC_LEVEL = 25

BATCH_SIZE = 1000

TABLE_STYLE = "steel_blue1"
ADMIN_STYLE = "red"
WORKSTATION_STYLE = "bold"
SERVER_STYLE = "bold chartreuse2"
DC_STYLE = "bold red"
RODC_STYLE = "bold orange3"
