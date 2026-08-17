from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    admin_id: int
    admin_username: str
    bot_token: str
    gemini_api_key: str
    port: int
    webhook_url: str
    gemini_model: str = "gemini-2.5-flash"
    database_path: str = "clinic.db"
    webhook_path_prefix: str = "/webhook"

    @property
    def webhook_path(self) -> str:
        return f"{self.webhook_path_prefix}/{self.bot_token}"

    @property
    def webhook_full_url(self) -> str:
        return f"{self.webhook_url.rstrip('/')}{self.webhook_path}"


def load_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set")

    raw_admin_id = os.getenv("ADMIN_ID", "").strip()
    if not raw_admin_id.isdigit():
        raise RuntimeError("ADMIN_ID must be an integer")

    webhook_url = os.getenv("WEBHOOK_URL", "").strip()
    if not webhook_url:
        raise RuntimeError("WEBHOOK_URL is not set")

    return Settings(
        admin_id=int(raw_admin_id),
        admin_username=os.getenv("ADMIN_USERNAME", "").strip(),
        bot_token=bot_token,
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        port=int(os.getenv("PORT", "8080")),
        webhook_url=webhook_url,
        database_path=os.getenv("DB_PATH", "clinic.db"),
    )


SETTINGS = load_settings()
