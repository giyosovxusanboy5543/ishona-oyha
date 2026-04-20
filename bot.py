import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers import user, admin
from db import init_db, set_role

API_TOKEN = os.getenv("BOT_TOKEN")
SUPER_ADMIN = 2034709966

async def main():
    if not API_TOKEN:
        raise ValueError("BOT_TOKEN yo‘q")

    init_db()
    set_role(SUPER_ADMIN, "super_admin")

    bot = Bot(token=API_TOKEN,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(user.router)
    dp.include_router(admin.router)

    print("🚀 BOT ISHGA TUSHDI")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
