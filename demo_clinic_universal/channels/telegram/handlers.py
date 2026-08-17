from __future__ import annotations

import logging

from aiogram import Bot, Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from config.clinic import CLINIC_NAME
from core import ApplicationService, BookingService, ClinicService, GeminiAI
from core.models import IncomingMessage, SessionState
from database import Database
from utils.validators import valid_name
from .keyboards import (
    address_menu,
    confirmation_menu,
    date_cancel_menu,
    main_menu,
    phone_keyboard,
    remove_reply_keyboard,
    service_details_menu,
    services_menu,
)

logger = logging.getLogger(__name__)


def build_router(
    db: Database,
    booking: BookingService,
    applications: ApplicationService,
    clinic: ClinicService,
    ai: GeminiAI,
    bot: Bot,
    admin_id: int,
) -> Router:
    router = Router(name="telegram")

    async def send_home(message: Message) -> None:
        await message.answer(clinic.welcome(), reply_markup=main_menu())

    @router.message(CommandStart())
    async def start(message: Message) -> None:
        if not message.from_user:
            return
        db.upsert_user(
            "telegram",
            str(message.from_user.id),
            message.from_user.username,
            message.from_user.first_name,
        )
        await message.answer(clinic.welcome(), reply_markup=main_menu())

    @router.message(Command("menu"))
    async def menu(message: Message) -> None:
        await send_home(message)

    @router.callback_query(F.data == "menu:home")
    async def menu_home(callback: CallbackQuery) -> None:
        await callback.answer()
        if not callback.message:
            return
        await callback.message.edit_text(clinic.welcome(), reply_markup=main_menu())

    @router.callback_query(F.data == "menu:services")
    async def menu_services(callback: CallbackQuery) -> None:
        await callback.answer()
        if not callback.message:
            return
        await callback.message.edit_text(
            "🩺 <b>Услуги и цены</b>\n\nВыберите услугу:",
            parse_mode="HTML",
            reply_markup=services_menu(),
        )

    @router.callback_query(F.data == "menu:address")
    async def menu_address(callback: CallbackQuery) -> None:
        await callback.answer()
        if not callback.message:
            return
        text, map_url = clinic.address()
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=address_menu(map_url))

    @router.callback_query(F.data == "menu:book")
    async def menu_book(callback: CallbackQuery) -> None:
        await callback.answer()
        if not callback.message:
            return
        await callback.message.edit_text(
            "📅 <b>Запись на приём</b>\n\nВыберите услугу:",
            parse_mode="HTML",
            reply_markup=services_menu(),
        )

    @router.callback_query(F.data.startswith("service:"))
    async def service_details(callback: CallbackQuery) -> None:
        await callback.answer()
        if not callback.message or not callback.data:
            return
        service_id = callback.data.split(":", 1)[1]
        text = clinic.service_details(service_id)
        if not text:
            await callback.message.answer("Услуга не найдена. Откройте список услуг ещё раз.")
            return
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=service_details_menu(service_id),
        )

    @router.callback_query(F.data.startswith("book:"))
    async def start_booking(callback: CallbackQuery) -> None:
        await callback.answer()
        if not callback.message or not callback.from_user or not callback.data:
            return
        service_id = callback.data.split(":", 1)[1]
        incoming = IncomingMessage(
            platform="telegram",
            user_id=str(callback.from_user.id),
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
        )
        response = booking.start(incoming, service_id)
        await callback.message.edit_text(response.text, reply_markup=date_cancel_menu())

    @router.callback_query(F.data == "booking:cancel")
    async def booking_cancel(callback: CallbackQuery) -> None:
        await callback.answer("Запись отменена")
        if not callback.message or not callback.from_user:
            return
        incoming = IncomingMessage(
            platform="telegram",
            user_id=str(callback.from_user.id),
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
        )
        response = booking.cancel(incoming)
        await callback.message.edit_text(response.text, reply_markup=main_menu())

    @router.callback_query(F.data == "booking:confirm")
    async def booking_confirm(callback: CallbackQuery) -> None:
        await callback.answer("Заявка создана")
        if not callback.message or not callback.from_user:
            return
        incoming = IncomingMessage(
            platform="telegram",
            user_id=str(callback.from_user.id),
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
        )
        application_id = booking.confirm(incoming)
        if not application_id:
            await callback.message.answer("Не удалось создать заявку. Пожалуйста, начните запись заново.", reply_markup=main_menu())
            return

        admin_text = applications.build_admin_text(application_id)
        if not admin_text:
            await callback.message.answer("Заявка создана, но не удалось подготовить уведомление менеджеру.", reply_markup=main_menu())
            return

        try:
            await bot.send_message(
                chat_id=admin_id,
                text=admin_text,
                parse_mode="HTML",
                reply_markup=__import__("channels.telegram.keyboards", fromlist=["admin_application_menu"]).admin_application_menu(application_id),
            )
        except Exception:
            logger.exception("Failed to notify administrator for application %s", application_id)
            await callback.message.answer(
                "Заявка сохранена, но уведомление менеджеру сейчас не удалось отправить. Мы не потеряли заявку.",
                reply_markup=main_menu(),
            )
            return

        await callback.message.edit_text(
            "Спасибо! ✅\n\nЗаявка отправлена в клинику.\nМенеджер свяжется с вами для подтверждения времени.",
            reply_markup=main_menu(),
        )

    @router.callback_query(F.data == "booking:edit")
    async def booking_edit(callback: CallbackQuery) -> None:
        await callback.answer()
        if not callback.message or not callback.from_user:
            return
        db.clear_session("telegram", str(callback.from_user.id))
        await callback.message.edit_text(
            "Выберите услугу заново:",
            reply_markup=services_menu(),
        )

    @router.callback_query(F.data.startswith("admin:"))
    async def admin_action(callback: CallbackQuery) -> None:
        if not callback.from_user or callback.from_user.id != admin_id:
            await callback.answer("У вас нет прав для этого действия.", show_alert=True)
            return
        if not callback.data:
            return
        _, action, raw_id = callback.data.split(":", 2)
        try:
            application_id = int(raw_id)
        except ValueError:
            await callback.answer("Некорректный ID заявки.", show_alert=True)
            return

        ok, user_id = applications.process_admin_action(application_id, action)
        if not ok or not user_id:
            await callback.answer("Заявка уже обработана или не найдена.", show_alert=True)
            return

        if action == "confirm":
            user_text = "✅ Ваша заявка подтверждена.\n\nМенеджер свяжется с вами для уточнения времени."
            admin_text = "✅ Заявка подтверждена."
        else:
            user_text = "Заявка отклонена.\n\nМенеджер свяжется с вами дополнительно."
            admin_text = "❌ Заявка отклонена."

        try:
            await bot.send_message(int(user_id), user_text, reply_markup=main_menu())
        except Exception:
            logger.exception("Could not notify applicant %s", user_id)
        await callback.answer(admin_text)
        if callback.message:
            await callback.message.edit_reply_markup(reply_markup=None)

    @router.message(F.contact)
    async def contact(message: Message) -> None:
        if not message.from_user or not message.contact:
            return
        user_id = str(message.from_user.id)
        phone = message.contact.phone_number
        if message.contact.user_id and message.contact.user_id != message.from_user.id:
            await message.answer("Пожалуйста, отправьте именно свой номер телефона.")
            return
        incoming = IncomingMessage(
            platform="telegram",
            user_id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            phone=phone,
            contact_shared=True,
        )
        response = booking.handle_phone(incoming)
        if response:
            await message.answer(response.text, reply_markup=confirmation_menu())
        else:
            await message.answer("Сейчас номер телефона не ожидается. Откройте запись через меню.", reply_markup=main_menu())

    @router.message(F.text)
    async def text_message(message: Message) -> None:
        if not message.from_user or not message.text:
            return
        user_id = str(message.from_user.id)
        text = message.text.strip()
        db.upsert_user("telegram", user_id, message.from_user.username, message.from_user.first_name)
        row = db.get_session("telegram", user_id)

        if row and row["current_state"] != SessionState.IDLE.value:
            if row["current_state"] == SessionState.WAITING_FOR_NAME.value and not valid_name(text):
                await message.answer("Введите, пожалуйста, имя без цифр, например: «Анна». ")
                return
            response = booking.handle_text(IncomingMessage(
                platform="telegram",
                user_id=user_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                text=text,
            ))
            if response:
                if response.request_phone:
                    await message.answer(response.text, reply_markup=phone_keyboard())
                else:
                    await message.answer(response.text, reply_markup=confirmation_menu() if "Всё верно" in response.text else date_cancel_menu())
                return

        lowered = text.lower()
        if any(phrase in lowered for phrase in ("хочу записаться", "запиши меня", "можно записаться", "хочу на приём", "хочу на прием")):
            await message.answer("Конечно 👍\n\nВыберите услугу:", reply_markup=services_menu())
            return

        # Deterministic service mention is handled before AI.
        for service in clinic.services():
            aliases = [service.name.lower(), service.name.lower().replace("профессиональная ", "")]
            if any(alias in lowered for alias in aliases):
                if any(token in lowered for token in ("сколько", "цена", "стоит", "стоимость")):
                    await message.answer(
                        f"{service.name} стоит <b>{service.price}</b>.\n\nХотите записаться?",
                        parse_mode="HTML",
                        reply_markup=service_details_menu(service.id),
                    )
                    return
                if any(token in lowered for token in ("можно", "хочу", "записаться", "запиши")):
                    incoming = IncomingMessage("telegram", user_id, message.from_user.username, message.from_user.first_name)
                    response = booking.start(incoming, service.id)
                    await message.answer(response.text, reply_markup=date_cancel_menu())
                    return

        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        answer = await ai.answer_customer(text)
        if answer:
            await message.answer(answer, reply_markup=main_menu())
        else:
            await message.answer(
                "Сейчас я не могу ответить на этот вопрос автоматически.\n\n"
                "Могу показать услуги или помочь оформить запись.",
                reply_markup=main_menu(),
            )

    @router.message()
    async def unsupported(message: Message) -> None:
        await message.answer(
            "Я лучше всего работаю с текстом и записью на приём.\n\nВыберите действие:",
            reply_markup=main_menu(),
        )

    return router
