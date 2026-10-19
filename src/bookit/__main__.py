import asyncio
import contextlib
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from bookit.bot.handlers import build_root_router
from bookit.bot.i18n import get_translator
from bookit.bot.middlewares import ServicesMiddleware
from bookit.config import Settings
from bookit.db.session import create_engine, create_sessionmaker
from bookit.logging_setup import setup_logging

logger = logging.getLogger("bookit")

COMMAND_NAMES = ("start", "help", "cancel")


def bot_commands() -> list[BotCommand]:
    tr = get_translator()
    return [BotCommand(command=name, description=tr(f"cmd.{name}")) for name in COMMAND_NAMES]


async def main() -> None:
    settings = Settings()  # type: ignore[call-arg]  # values come from the environment
    setup_logging(settings.log_level)
    schedule_cfg = settings.schedule_config()

    engine = create_engine(settings.database_url)
    sessionmaker = create_sessionmaker(engine)

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.outer_middleware(ServicesMiddleware(sessionmaker, schedule_cfg, settings.admin_ids))
    dp.include_router(build_root_router())

    if not settings.admin_ids:
        logger.warning("ADMIN_IDS is not set — the admin panel will be unavailable")

    try:
        await bot.set_my_commands(bot_commands())
        logger.info("Bot started")
        await dp.start_polling(
            bot,
            admin_ids=settings.admin_ids,
            schedule_cfg=schedule_cfg,
        )
    finally:
        await bot.session.close()
        await engine.dispose()
        logger.info("Bot stopped")


def run() -> None:
    # Ctrl+C is a normal way to stop the bot — no traceback needed
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())


if __name__ == "__main__":
    run()
