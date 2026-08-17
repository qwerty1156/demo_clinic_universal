from __future__ import annotations

import re

from config.clinic import get_service
from core.models import IncomingMessage, OutgoingMessage, SessionState
from database import Database


class BookingService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def start(self, message: IncomingMessage, service_id: str | None = None) -> OutgoingMessage:
        self.db.upsert_user(message.platform, message.user_id, message.username, message.first_name)
        self.db.clear_session(message.platform, message.user_id)
        if service_id:
            service = get_service(service_id)
            if not service:
                return OutgoingMessage("Не удалось найти эту услугу. Откройте список услуг ещё раз.")
            self.db.upsert_session(
                message.platform,
                message.user_id,
                current_state=SessionState.WAITING_FOR_DATE.value,
                service_id=service_id,
            )
            return OutgoingMessage(f"Отлично 👍\n\nНа какой день вам было бы удобно прийти?")

        self.db.upsert_session(
            message.platform,
            message.user_id,
            current_state=SessionState.IDLE.value,
        )
        return OutgoingMessage("Выберите услугу, с которой хотите начать запись.")

    def handle_text(self, message: IncomingMessage) -> OutgoingMessage | None:
        row = self.db.get_session(message.platform, message.user_id)
        if not row or row["current_state"] == SessionState.IDLE.value:
            return None

        text = (message.text or "").strip()
        state = row["current_state"]

        if state == SessionState.WAITING_FOR_DATE.value:
            if not text:
                return OutgoingMessage("Напишите, пожалуйста, желаемую дату или ориентир, например: «в пятницу».")
            self.db.upsert_session(
                message.platform,
                message.user_id,
                desired_date=text,
                current_state=SessionState.WAITING_FOR_NAME.value,
            )
            return OutgoingMessage("Хорошо 👍\n\nКак вас зовут?")

        if state == SessionState.WAITING_FOR_NAME.value:
            if len(text) < 2:
                return OutgoingMessage("Напишите, пожалуйста, имя немного подробнее.")
            self.db.upsert_session(
                message.platform,
                message.user_id,
                name=text,
                current_state=SessionState.WAITING_FOR_PHONE.value,
            )
            return OutgoingMessage(
                "Спасибо! 😊\n\nТеперь отправьте номер телефона для связи.",
                request_phone=True,
            )

        if state == SessionState.WAITING_FOR_PHONE.value:
            phone = normalize_phone(text)
            if not phone:
                return OutgoingMessage(
                    "Не удалось распознать номер. Отправьте его в формате +7XXXXXXXXXX или воспользуйтесь кнопкой отправки контакта.",
                    request_phone=True,
                )
            return self._save_phone_and_confirm(message, phone)

        if state == SessionState.CONFIRMING_BOOKING.value:
            return OutgoingMessage("Используйте кнопки ниже, чтобы подтвердить или изменить заявку.")

        return None

    def handle_phone(self, message: IncomingMessage) -> OutgoingMessage | None:
        row = self.db.get_session(message.platform, message.user_id)
        if not row or row["current_state"] != SessionState.WAITING_FOR_PHONE.value:
            return None
        phone = normalize_phone(message.phone or "")
        if not phone:
            return OutgoingMessage("Не удалось распознать номер. Попробуйте отправить его ещё раз.", request_phone=True)
        return self._save_phone_and_confirm(message, phone)

    def _save_phone_and_confirm(self, message: IncomingMessage, phone: str) -> OutgoingMessage:
        row = self.db.get_session(message.platform, message.user_id)
        service = get_service(row["service_id"] if row else "")
        if not row or not service:
            self.db.clear_session(message.platform, message.user_id)
            return OutgoingMessage("Сессия записи устарела. Начните запись заново.")
        self.db.upsert_user(message.platform, message.user_id, message.username, message.first_name, phone)
        self.db.upsert_session(
            message.platform,
            message.user_id,
            phone=phone,
            current_state=SessionState.CONFIRMING_BOOKING.value,
        )
        row = self.db.get_session(message.platform, message.user_id)
        summary = (
            "Проверьте данные заявки:\n\n"
            f"Услуга: {service.name}\n"
            f"Дата: {row['desired_date']}\n"
            f"Имя: {row['name']}\n"
            f"Телефон: {phone}\n\n"
            "Всё верно?"
        )
        return OutgoingMessage(summary)

    def confirm(self, message: IncomingMessage) -> int | None:
        row = self.db.get_session(message.platform, message.user_id)
        if not row or row["current_state"] != SessionState.CONFIRMING_BOOKING.value:
            return None
        service = get_service(row["service_id"])
        if not service or not row["desired_date"] or not row["name"] or not row["phone"]:
            return None
        application_id = self.db.create_application(
            platform=message.platform,
            platform_user_id=message.user_id,
            service_id=service.id,
            service_name=service.name,
            desired_date=row["desired_date"],
            name=row["name"],
            phone=row["phone"],
            username=message.username,
        )
        self.db.clear_session(message.platform, message.user_id)
        return application_id

    def cancel(self, message: IncomingMessage) -> OutgoingMessage:
        self.db.clear_session(message.platform, message.user_id)
        return OutgoingMessage("Запись отменена. Вы можете начать новую в любое время.")


def normalize_phone(value: str) -> str | None:
    digits = re.sub(r"\D", "", value)
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    if len(digits) == 11 and digits.startswith("7"):
        return "+" + digits
    return None
