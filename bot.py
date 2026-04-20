import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers import user, admin
from db import init_db, set_role, get_role

# ❗ Railway uchun dotenv shart emas (lekin qolsa ham zarar yo‘q)
from dotenv import load_dotenv
load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")

SUPER_ADMIN = 2034709966

logging.basicConfig(level=logging.INFO)


async def main():
    # ❗ TOKEN
    if not API_TOKEN:
        raise ValueError("❌ BOT_TOKEN topilmadi")

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

    # 🤖 BOT
    bot = Bot(
        token=API_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())

    # 🔗 ROUTERLAR
    dp.include_router(user.router)
    dp.include_router(admin.router)

    # 🔥 GLOBAL ERROR HANDLER (server uchun)
    @dp.errors()
    async def error_handler(update, exception):
        print("❌ ERROR:", exception)
        return True

    # 🔍 DEBUG
    print("=================================")
    print("🚀 BOT ISHGA TUSHDI")
    print("SUPER ADMIN:", SUPER_ADMIN)
    print("ROLE:", get_role(SUPER_ADMIN))
    print("=================================")

    # ▶️ START
    await dp.start_polling(bot)


# 🔥 SERVERDA BOT O‘CHIB QOLMASLIGI UCHUN
if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            print("🔁 RESTART:", e)
