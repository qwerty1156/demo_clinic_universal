from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SessionState(str, Enum):
    IDLE = "idle"
    WAITING_FOR_DATE = "waiting_for_date"
    WAITING_FOR_NAME = "waiting_for_name"
    WAITING_FOR_PHONE = "waiting_for_phone"
    CONFIRMING_BOOKING = "confirming_booking"


class ApplicationStatus(str, Enum):
    NEW = "new"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class IncomingMessage:
    platform: str
    user_id: str
    username: str | None = None
    first_name: str | None = None
    text: str | None = None
    phone: str | None = None
    contact_shared: bool = False
    callback_data: str | None = None
    callback_id: str | None = None


@dataclass(slots=True)
class OutgoingMessage:
    text: str
    keyboard: list[list[dict[str, Any]]] | None = None
    parse_mode: str | None = None
    request_phone: bool = False


@dataclass(slots=True)
class AdminAction:
    application_id: int
    action: str
