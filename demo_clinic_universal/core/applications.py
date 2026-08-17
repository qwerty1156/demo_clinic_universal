from __future__ import annotations

from datetime import datetime
from html import escape
import logging

from database import Database

logger = logging.getLogger(__name__)


class ApplicationService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def build_admin_text(self, application_id: int) -> str | None:
        row = self.db.get_application(application_id)
        if not row:
            return None
        username = f"@{row['username']}" if row["username"] else "—"
        created = datetime.fromisoformat(row["created_at"]).astimezone().strftime("%d.%m.%Y %H:%M")
        return (
            "🔔 <b>НОВАЯ ЗАЯВКА</b>\n\n"
            f"👤 Имя: {escape(row['name'])}\n"
            f"📞 Телефон: {escape(row['phone'])}\n\n"
            f"🩺 Услуга: {escape(row['service_name'])}\n"
            f"📅 Желаемая дата: {escape(row['desired_date'])}\n\n"
            f"📱 Платформа: {escape(row['platform'])}\n"
            f"🆔 User ID: {escape(row['platform_user_id'])}\n"
            f"👤 Username: {escape(username)}\n\n"
            f"⏰ Создана: {created}"
        )

    def process_admin_action(self, application_id: int, action: str) -> tuple[bool, str | None]:
        status = "confirmed" if action == "confirm" else "rejected"
        ok = self.db.update_application_status(application_id, status)
        if not ok:
            return False, None
        row = self.db.get_application(application_id)
        return True, str(row["platform_user_id"]) if row else None
