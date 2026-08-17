from __future__ import annotations

import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from settings import SETTINGS
from channels.telegram.handlers import build_router
from channels.telegram.webhook import create_web_app
from core import ApplicationService, BookingService, ClinicService, GeminiAI
from database import Database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("demo-clinic")


async def main() -> None:
    db = Database(SETTINGS.database_path)
    bot = Bot(
        token=SETTINGS.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    clinic = ClinicService()
    booking = BookingService(db)
    applications = ApplicationService(db)
    ai = GeminiAI(SETTINGS)

    router = build_router(
        db=db,
        booking=booking,
        applications=applications,
        clinic=clinic,
        ai=ai,
        bot=bot,
        admin_id=SETTINGS.admin_id,
    )
    dp.include_router(router)

    webhook_url = SETTINGS.webhook_full_url
    logger.info("Setting webhook: %s", webhook_url)
    await bot.delete_webhook(drop_pending_updates=False)
    await bot.set_webhook(url=webhook_url, drop_pending_updates=False)

    app = create_web_app(bot, dp, SETTINGS.webhook_path)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=SETTINGS.port)
    await site.start()
    logger.info("Web server listening on 0.0.0.0:%s", SETTINGS.port)
    logger.info("Webhook path: %s", SETTINGS.webhook_path)

    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped")
