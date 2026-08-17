from __future__ import annotations

from typing import Any

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

from channels.base import ChannelAdapter
from core.models import OutgoingMessage


class TelegramAdapter(ChannelAdapter):
    def __init__(self, bot: Bot, admin_id: int) -> None:
        self.bot = bot
        self.admin_id = admin_id

    @staticmethod
    def _inline(keyboard: list[list[dict[str, Any]]] | None) -> InlineKeyboardMarkup | None:
        if not keyboard:
            return None
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(**button) for button in row]
                for row in keyboard
            ]
        )

    async def send_message(self, user_id: str, message: OutgoingMessage, **kwargs: Any) -> Message:
        return await self.bot.send_message(
            chat_id=int(user_id),
            text=message.text,
            parse_mode=message.parse_mode,
            reply_markup=kwargs.get("reply_markup"),
        )

    async def send_admin_message(self, message: str, application_id: int) -> Message:
        from channels.telegram.keyboards import admin_application_menu
        return await self.bot.send_message(
            chat_id=self.admin_id,
            text=message,
            parse_mode="HTML",
            reply_markup=admin_application_menu(application_id),
        )

    async def answer_callback(self, callback_id: str, text: str | None = None, show_alert: bool = False) -> None:
        await self.bot.answer_callback_query(callback_id, text=text, show_alert=show_alert)
