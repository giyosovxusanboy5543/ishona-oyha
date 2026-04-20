from aiogram import Router, F
from aiogram.types import *
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import get_appeal, update_status, get_admins

router = Router()

# ================= CHECK ADMIN =================
def is_admin(uid):
    return uid in get_admins()

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
    await call.answer()

    if not is_admin(call.from_user.id):
        await call.message.answer("❌ Ruxsat yo‘q")
        return

    cid = call.data.split("_")[1]
    ap = get_appeal(cid)

    if not ap:
        await call.message.answer("❌ Topilmadi")
        return

    await state.update_data(cid=cid)
    await call.message.answer("👤 Ism familya:")
    await state.set_state(Answer.name)


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
    if not (m.document or m.photo):
        await m.answer("❗ Fayl yuborish majburiy")
        return

    data = await state.get_data()
    cid = data["cid"]

    ap = get_appeal(cid)
    if not ap:
        await m.answer("❌ Topilmadi")
        return

    text = f"""📨 JAVOB
🆔 {cid}

👤 {data['name']}
💼 {data['job']}
📞 {data['phone']}
"""

    await m.bot.send_message(ap[2], text)

    if m.document:
        await m.bot.send_document(ap[2], m.document.file_id)
    elif m.photo:
        await m.bot.send_photo(ap[2], m.photo[-1].file_id)

    await m.answer("✅ Yuborildi")
    await state.clear()


# ================= QABUL =================
@router.callback_query(F.data.startswith("ok_"))
async def ok(call: CallbackQuery):
    await call.answer()

    if not is_admin(call.from_user.id):
        await call.message.answer("❌ Ruxsat yo‘q")
        return

    cid = call.data.split("_")[1]
    ap = get_appeal(cid)

    if not ap:
        await call.message.answer("❌ Topilmadi")
        return

    update_status(cid, "Jarayonda")

    await call.bot.send_message(
        ap[2],
        f"⏳ Jarayonda\n🆔 {cid}"
    )

    await call.message.answer("✅ Qabul qilindi")


# ================= RAD =================
@router.callback_query(F.data.startswith("no_"))
async def no(call: CallbackQuery):
    await call.answer()

    if not is_admin(call.from_user.id):
        await call.message.answer("❌ Ruxsat yo‘q")
        return

    cid = call.data.split("_")[1]
    ap = get_appeal(cid)

    if not ap:
        await call.message.answer("❌ Topilmadi")
        return

    update_status(cid, "Rad etildi")

    await call.bot.send_message(
        ap[2],
        f"❌ Rad etildi\n🆔 {cid}"
    )

    await call.message.answer("❌ Rad etildi")


# ================= DEBUG =================
@router.callback_query()
async def debug(call: CallbackQuery):
    print("CLICK:", call.data)
