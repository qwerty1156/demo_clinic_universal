from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core.models import OutgoingMessage


class ChannelAdapter(ABC):
    """Transport-level interface. Core must not depend on Telegram/WhatsApp/Instagram."""

    @abstractmethod
    async def send_message(self, user_id: str, message: OutgoingMessage, **kwargs: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def send_admin_message(self, message: str, application_id: int) -> Any:
        raise NotImplementedError
