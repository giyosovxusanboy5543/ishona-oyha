import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import user, admin
from db import init_db, set_role

# 🔥 ENV (Railway Variables)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🔥 SUPER ADMIN
SUPER_ADMIN = 2034709966

# 🔥 LOGGING (PRO)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


# ================= MAIN =================
async def main():
    # ❗ TOKEN CHECK
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN topilmadi")
        sys.exit(1)

    # 🔥 DB INIT
    try:
        init_db()
        logger.info("✅ Database ishga tayyor")
    except Exception as e:
        logger.error(f"❌ DB ERROR: {e}")

    # 🔥 SUPER ADMIN INIT
    try:
        set_role(SUPER_ADMIN, "super_admin")
        logger.info(f"👑 Super admin o‘rnatildi: {SUPER_ADMIN}")
    except Exception as e:
        logger.error(f"❌ ADMIN ERROR: {e}")

    # 🤖 BOT INIT
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())

    # 🔗 ROUTERLAR (MUHIM)
    dp.include_router(user.router)
    dp.include_router(admin.router)

    # 🔥 GLOBAL ERROR HANDLER
    @dp.errors()
    async def error_handler(update, exception):
        logger.error(f"❌ GLOBAL ERROR: {exception}")
        return True

    logger.info("=================================")
    logger.info("🚀 BOT ISHGA TUSHDI (PRODUCTION)")
    logger.info("=================================")

    # 🔥 POLLING
    await dp.start_polling(bot)


# ================= AUTO RESTART =================
async def run():
    while True:
        try:
            await main()
        except Exception as e:
            logger.error(f"🔁 RESTART: {e}")
            await asyncio.sleep(3)


# ================= START =================
if __name__ == "__main__":
    try:
        asyncio.run(run())
    except (KeyboardInterrupt, SystemExit):
        logger.info("⛔ Bot to‘xtatildi")
