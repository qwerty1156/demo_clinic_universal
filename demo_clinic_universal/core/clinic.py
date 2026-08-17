from __future__ import annotations

from config.clinic import (
    CLINIC_ADDRESS,
    CLINIC_DESCRIPTION,
    CLINIC_MAP_URL,
    CLINIC_NAME,
    CLINIC_SCHEDULE,
    SERVICES,
    get_service,
)


class ClinicService:
    @staticmethod
    def welcome() -> str:
        return (
            f"Здравствуйте! 👋\n\n"
            f"Добро пожаловать в {CLINIC_NAME}.\n"
            "Я помогу узнать информацию об услугах и записаться на приём."
        )

    @staticmethod
    def services() -> tuple:
        return SERVICES

    @staticmethod
    def service_details(service_id: str) -> str | None:
        service = get_service(service_id)
        if not service:
            return None
        return (
            f"<b>{service.name}</b>\n\n"
            f"💰 Цена: <b>{service.price}</b>\n"
            f"ℹ️ {service.description}"
        )

    @staticmethod
    def address() -> tuple[str, str]:
        text = (
            f"📍 <b>Адрес</b>\n{CLINIC_ADDRESS}\n\n"
            f"🕐 <b>График</b>\n{CLINIC_SCHEDULE}"
        )
        return text, CLINIC_MAP_URL

    @staticmethod
    def description() -> str:
        return CLINIC_DESCRIPTION
