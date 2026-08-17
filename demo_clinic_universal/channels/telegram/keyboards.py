from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from config.clinic import SERVICES


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🩺 Услуги и цены", callback_data="menu:services")],
            [InlineKeyboardButton(text="📅 Записаться", callback_data="menu:book")],
            [InlineKeyboardButton(text="📍 Адрес и график", callback_data="menu:address")],
        ]
    )


def services_menu() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{service.name} — {service.price}", callback_data=f"service:{service.id}")]
        for service in SERVICES
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def service_details_menu(service_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Записаться", callback_data=f"book:{service_id}")],
            [InlineKeyboardButton(text="⬅️ К услугам", callback_data="menu:services")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:home")],
        ]
    )


def date_cancel_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="booking:cancel")]]
    )


def confirmation_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Всё верно", callback_data="booking:confirm"),
                InlineKeyboardButton(text="✏️ Изменить", callback_data="booking:edit"),
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="booking:cancel")],
        ]
    )


def phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def remove_reply_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove(remove_keyboard=True)


def address_menu(map_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗺 Открыть на карте", url=map_url)],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:home")],
        ]
    )


def admin_application_menu(application_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin:confirm:{application_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin:reject:{application_id}"),
            ]
        ]
    )
