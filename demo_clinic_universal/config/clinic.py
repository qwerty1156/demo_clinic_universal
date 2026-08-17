from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class Service:
    id: str
    name: str
    price: str
    description: str


CLINIC_NAME: Final = "Демо Клиника"
CLINIC_DESCRIPTION: Final = (
    "Современный медицинский центр с удобной записью и внимательным сервисом."
)
CLINIC_ADDRESS: Final = "г. Алматы, ул. Примерная, 10"
CLINIC_SCHEDULE: Final = "Пн–Пт: 09:00–20:00\nСб: 10:00–18:00\nВс: выходной"
CLINIC_MAP_URL: Final = "https://maps.google.com/?q=Алматы+ул.+Примерная+10"

SERVICES: Final[tuple[Service, ...]] = (
    Service("consultation", "Консультация специалиста", "10 000 ₸", "Первичная консультация и обсуждение дальнейшего плана."),
    Service("cleaning", "Профессиональная чистка", "15 000 ₸", "Профессиональная гигиена полости рта."),
    Service("whitening", "Отбеливание", "35 000 ₸", "Эстетическая процедура отбеливания. Возможны индивидуальные ограничения."),
    Service("caries", "Лечение кариеса", "от 20 000 ₸", "Стоимость зависит от объёма лечения и определяется после осмотра."),
)


def services_as_text() -> str:
    return "\n".join(f"• {service.name} — {service.price}" for service in SERVICES)


def get_service(service_id: str) -> Service | None:
    return next((service for service in SERVICES if service.id == service_id), None)


def clinic_context() -> str:
    return (
        f"Название: {CLINIC_NAME}\n"
        f"Описание: {CLINIC_DESCRIPTION}\n"
        f"Адрес: {CLINIC_ADDRESS}\n"
        f"График:\n{CLINIC_SCHEDULE}\n"
        f"Услуги:\n{services_as_text()}"
    )
