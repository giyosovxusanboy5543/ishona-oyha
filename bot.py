import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers import user, admin
from db import init_db, set_role, get_role

from dotenv import load_dotenv
load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
SUPER_ADMIN = 2034709966

# 🔥 LOGGING (PRO LEVEL)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

# 🔥 GLOBAL FLAG (duplicate polling oldini oladi)
is_running = False


async def main():
    global is_running

    if is_running:
        logger.warning("⚠️ Bot allaqachon ishlayapti!")
        return

    is_running = True

    if not API_TOKEN:
        raise ValueError("❌ BOT_TOKEN topilmadi")

    # 🔥 DB INIT
    try:
        init_db()
        logger.info("✅ Database tayyor")
    except Exception as e:
        logger.error(f"❌ DB ERROR: {e}")

    # 🔥 ADMIN INIT
    try:
        set_role(SUPER_ADMIN, "super_admin")
        logger.info(f"👑 Super admin: {SUPER_ADMIN}")
    except Exception as e:
        logger.error(f"❌ ADMIN ERROR: {e}")

    bot = Bot(
        token=API_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())

    # 🔗 ROUTERLAR
    dp.include_router(user.router)
    dp.include_router(admin.router)

    # 🔥 GLOBAL ERROR HANDLER
    @dp.errors()
    async def error_handler(update, exception):
        logger.error(f"❌ GLOBAL ERROR: {exception}")
        return True

    logger.info("=================================")
    logger.info("🚀 BOT ISHGA TUSHDI (PRO SERVER)")
    logger.info(f"ROLE: {get_role(SUPER_ADMIN)}")
    logger.info("=================================")

    try:
        await dp.start_polling(bot)
    finally:
        is_running = False


# 🔥 AUTO RESTART SYSTEM (SERVER UCHUN)
if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            logger.error(f"🔁 RESTART: {e}")
            try:
                asyncio.sleep(3)
            except:
                pass
