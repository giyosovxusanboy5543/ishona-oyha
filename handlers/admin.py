from aiogram import Router, F
from aiogram.types import *
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import get_appeal, update_status, is_admin

router = Router()

# ================= TUGMALAR =================
def buttons(cid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Qabul", callback_data=f"ok_{cid}")],
        [InlineKeyboardButton(text="✉️ Javob", callback_data=f"ans_{cid}")],
        [InlineKeyboardButton(text="❌ Rad", callback_data=f"no_{cid}")]
    ])

# ================= STATE =================
class Answer(StatesGroup):
    cid = State()
    name = State()
    job = State()
    phone = State()
    file = State()

# ================= JAVOB =================
@router.callback_query(F.data.startswith("ans_"))
async def answer_start(call: CallbackQuery, state: FSMContext):
    try:
        await call.answer()

        if not is_admin(call.from_user.id):
            return await call.message.answer("❌ Ruxsat yo‘q")

        cid = call.data.split("_")[1]
        ap = get_appeal(cid)

        if not ap:
            return await call.message.answer("❌ Topilmadi")

        await state.clear()
        await state.update_data(cid=cid)

        await call.message.answer("👤 Ism familya:")
        await state.set_state(Answer.name)

    except Exception as e:
        print("ERROR ans_start:", e)


@router.message(Answer.name)
async def a1(m: Message, state: FSMContext):
    await state.update_data(name=m.text)
    await m.answer("💼 Lavozim:")
    await state.set_state(Answer.job)


@router.message(Answer.job)
async def a2(m: Message, state: FSMContext):
    await state.update_data(job=m.text)
    await m.answer("📞 Telefon:")
    await state.set_state(Answer.phone)


@router.message(Answer.phone)
async def a3(m: Message, state: FSMContext):
    await state.update_data(phone=m.text)
    await m.answer("📎 Fayl yubor (majburiy)")
    await state.set_state(Answer.file)


@router.message(Answer.file)
async def a4(m: Message, state: FSMContext):
    try:
        if not (m.document or m.photo):
            return await m.answer("❗ Fayl yuborish majburiy")

        data = await state.get_data()
        cid = data["cid"]

        ap = get_appeal(cid)
        if not ap:
            return await m.answer("❌ Topilmadi")

        user_id = ap["user_id"]  # 🔥 FIX

        text = f"""📨 JAVOB
🆔 {cid}

👤 {data['name']}
💼 {data['job']}
📞 {data['phone']}
"""

        await m.bot.send_message(user_id, text)

        if m.document:
            await m.bot.send_document(user_id, m.document.file_id)
        elif m.photo:
            await m.bot.send_photo(user_id, m.photo[-1].file_id)

        await m.answer("✅ Yuborildi")
        await state.clear()

    except Exception as e:
        print("ERROR ANSWER:", e)


# ================= QABUL =================
@router.callback_query(F.data.startswith("ok_"))
async def ok(call: CallbackQuery):
    try:
        await call.answer()

        if not is_admin(call.from_user.id):
            return await call.message.answer("❌ Ruxsat yo‘q")

        cid = call.data.split("_")[1]
        ap = get_appeal(cid)

        if not ap:
            return await call.message.answer("❌ Topilmadi")

        update_status(cid, "Jarayonda")

        await call.bot.send_message(
            ap["user_id"],  # 🔥 FIX
            f"⏳ Jarayonda\n🆔 {cid}"
        )

        await call.message.answer("✅ Qabul qilindi")

    except Exception as e:
        print("ERROR OK:", e)


# ================= RAD =================
@router.callback_query(F.data.startswith("no_"))
async def no(call: CallbackQuery):
    try:
        await call.answer()

        if not is_admin(call.from_user.id):
            return await call.message.answer("❌ Ruxsat yo‘q")

        cid = call.data.split("_")[1]
        ap = get_appeal(cid)

        if not ap:
            return await call.message.answer("❌ Topilmadi")

        update_status(cid, "Rad etildi")

        await call.bot.send_message(
            ap["user_id"],  # 🔥 FIX
            f"❌ Rad etildi\n🆔 {cid}"
        )

        await call.message.answer("❌ Rad etildi")

    except Exception as e:
        print("ERROR NO:", e)


# ================= DEBUG =================
@router.callback_query()
async def debug(call: CallbackQuery):
    print("CLICK:", call.data)
