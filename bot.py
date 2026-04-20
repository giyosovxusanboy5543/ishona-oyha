import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import user, admin
from db import init_db, set_role

# 🔥 ENV (Railway uchun)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🔥 SENING TELEGRAM ID
SUPER_ADMIN = 2034709966

# 🔥 LOG
logging.basicConfig(level=logging.INFO)

async def main():
    # ❗ TOKEN TEKSHIRUV
    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN topilmadi")

    # 🔥 DATABASE
    init_db()

    # 🔥 SUPER ADMIN
    set_role(SUPER_ADMIN, "super_admin")

    # 🤖 BOT
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())

    # 🔗 ROUTERLAR
    dp.include_router(user.router)
    dp.include_router(admin.router)

    print("=================================")
    print("🚀 BOT ISHGA TUSHDI (SERVER)")
    print("=================================")

    # 🔥 ERROR HANDLER (MUHIM)
    @dp.errors()
    async def error_handler(update, exception):
        print("❌ ERROR:", exception)
        return True

    # ▶️ START
    await dp.start_polling(bot)


# 🔥 AUTO RESTART (SERVERDA YIQILMASIN)
if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            print("🔁 RESTART:", e)
