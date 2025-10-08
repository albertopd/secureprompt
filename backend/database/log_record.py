from enum import Enum
from dataclasses import dataclass
from typing import Any
from datetime import datetime, timezone


class LogRecordCategory(Enum):
    SECURITY = "auth"
    TEXT = "text"
    FILE = "file"


class LogRecordAction(Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    SCRUB = "scrub"
    DESCRUB = "descrub"
    DOWNLOAD = "download"


@dataclass
class LogRecord:
    corp_key: str
    category: LogRecordCategory
    action: LogRecordAction
    details: Any
    device_info: str
    browser_info: str
    client_ip: str
    user_agent: str
    timestamp: datetime = datetime.now(timezone.utc)