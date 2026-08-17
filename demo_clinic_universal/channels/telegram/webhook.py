from __future__ import annotations

import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import Update

logger = logging.getLogger(__name__)


def create_web_app(bot: Bot, dispatcher: Dispatcher, webhook_path: str) -> web.Application:
    app = web.Application()

    async def health(_: web.Request) -> web.Response:
        return web.Response(text="Bot is running!")

    async def telegram_webhook(request: web.Request) -> web.Response:
        try:
            if not request.content_type == "application/json":
                return web.Response(status=415, text="Unsupported Media Type")
            data = await request.json()
            update = Update.model_validate(data)
            await dispatcher.feed_update(bot, update)
            return web.Response(text="OK")
        except Exception:
            logger.exception("Webhook processing failed")
            # Telegram expects a successful HTTP response to avoid aggressive retries.
            return web.Response(text="OK")

    app.router.add_get("/", health)
    app.router.add_post(webhook_path, telegram_webhook)
    return app
