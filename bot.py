import asyncio
import logging
import os
import signal
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import user, admin
from db import init_db, set_role

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPER_ADMIN = 2034709966

# ================= LOG =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ================= MAIN =================
async def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN topilmadi (Railway Variables tekshir)")
        sys.exit(1)

    # 🔥 DB INIT
    try:
        init_db()
        logger.info("✅ Database tayyor")
    except Exception as e:
        logger.error(f"❌ DB ERROR: {e}")

    # 🔥 SUPER ADMIN
    try:
        set_role(SUPER_ADMIN, "super_admin")
        logger.info(f"👑 Super admin: {SUPER_ADMIN}")
    except Exception as e:
        logger.error(f"❌ ADMIN ERROR: {e}")

    # 🤖 BOT
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())

    # 🔗 ROUTERLAR (MUHIM)
    dp.include_router(user.router)
    dp.include_router(admin.router)

    # 🔥 ERROR HANDLER
    @dp.errors()
    async def error_handler(update, exception):
        logger.error(f"❌ GLOBAL ERROR: {exception}")
        return True

    logger.info("=================================")
    logger.info("🚀 BOT ISHGA TUSHDI (FULL PRO)")
    logger.info("=================================")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("🛑 Bot session yopildi")


# ================= RESTART =================
async def runner():
    while True:
        try:
            await main()
        except Exception as e:
            logger.error(f"🔁 RESTART: {e}")
            await asyncio.sleep(3)


# ================= SHUTDOWN =================
def shutdown():
    logger.warning("⛔ Bot to‘xtatilmoqda...")
    sys.exit(0)


# ================= START =================
if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda s, f: shutdown())
    signal.signal(signal.SIGTERM, lambda s, f: shutdown())

    try:
        asyncio.run(runner())
    except (KeyboardInterrupt, SystemExit):
        logger.info("⛔ Bot to‘xtadi")
