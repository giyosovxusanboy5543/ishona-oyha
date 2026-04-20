import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers import user, admin
from db import init_db, set_role, get_role

from dotenv import load_dotenv
load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")

# 🔥 BU YERGA O‘Z TELEGRAM ID INGNI QO‘Y
SUPER_ADMIN = 2034709966

logging.basicConfig(level=logging.INFO)


async def main():
    # ❗ TOKEN TEKSHIRUV
    if not API_TOKEN:
        raise ValueError("❌ BOT_TOKEN topilmadi (.env ni tekshir)")

    # 🔥 1️⃣ DATABASE YARATAMIZ
    init_db()

    # 🔥 2️⃣ SUPER ADMINNI YOZAMIZ
    set_role(SUPER_ADMIN, "super_admin")

    # 🤖 BOT
    bot = Bot(
        token=API_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())

    # 🔗 ROUTERLAR
    dp.include_router(user.router)
    dp.include_router(admin.router)

    # 🔍 DEBUG
    print("=================================")
    print("🚀 BOT ISHGA TUSHDI")
    print("SUPER ADMIN:", SUPER_ADMIN)
    print("ROLE:", get_role(SUPER_ADMIN))
    print("=================================")

    # ▶️ START
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot to‘xtatildi")