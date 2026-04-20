import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers import user, admin
from db import init_db, set_role

from dotenv import load_dotenv
load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
SUPER_ADMIN = 2034709966

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# 🔥 GLOBAL LOCK (duplicate polling oldini oladi)
is_running = False


async def main():
    global is_running

    if is_running:
        print("⚠️ Bot allaqachon ishlayapti")
        return

    is_running = True

    if not API_TOKEN:
        raise ValueError("❌ BOT_TOKEN yo‘q")

    # 🔥 DB INIT
    try:
        init_db()
        print("✅ DB OK")
    except Exception as e:
        print("❌ DB ERROR:", e)

    # 🔥 ADMIN INIT
    try:
        set_role(SUPER_ADMIN, "super_admin")
    except Exception as e:
        print("❌ ADMIN ERROR:", e)

    bot = Bot(
        token=API_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())

    # ❗ FAQAT 1 MARTA
    dp.include_router(user.router)
    dp.include_router(admin.router)

    # 🔥 GLOBAL ERROR HANDLER
    @dp.errors()
    async def error_handler(update, exception):
        print("❌ ERROR:", exception)
        return True

    print("=================================")
    print("🚀 BOT ISHGA TUSHDI (SERVER)")
    print("=================================")

    try:
        await dp.start_polling(bot)
    finally:
        is_running = False


# 🔥 AUTO RESTART (Railway uchun)
if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            print("🔁 RESTART:", e)
            asyncio.sleep(3)
