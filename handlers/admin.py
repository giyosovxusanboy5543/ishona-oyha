from aiogram import Router, F
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import get_appeal, update_status, get_admins, set_role, delete_admin

router = Router()

SUPER_ADMIN = 2034709966

# ================= ADMIN CHECK =================
def is_admin(uid):
    return uid in get_admins()

# ================= BUTTONS =================
def buttons(cid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Qabul", callback_data=f"ok:{cid}"),
            InlineKeyboardButton(text="❌ Rad", callback_data=f"no:{cid}")
        ],
        [
            InlineKeyboardButton(text="✉️ Javob", callback_data=f"ans:{cid}")
        ]
    ])

# ================= STATES =================
class AddAdmin(StatesGroup):
    uid = State()

class DeleteAdmin(StatesGroup):
    uid = State()

class Answer(StatesGroup):
    cid = State()
    name = State()
    job = State()
    phone = State()
    text = State()

class Reject(StatesGroup):
    cid = State()
    reason = State()

# ================= PANEL (/panel) =================
@router.message(Command("panel"))
async def panel(m: Message):
    if m.from_user.id != SUPER_ADMIN:
        return await m.answer("❌ Sizda ruxsat yo‘q")

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Admin qo‘shish")],
            [KeyboardButton(text="➖ Admin o‘chirish")]
        ],
        resize_keyboard=True
    )

    await m.answer("⚙️ SUPER ADMIN PANEL", reply_markup=kb)

# ================= ADD ADMIN =================
@router.message(F.text == "➕ Admin qo‘shish")
async def add_start(m: Message, state: FSMContext):
    if m.from_user.id != SUPER_ADMIN:
        return

    await m.answer("🆔 Admin ID kiriting:")
    await state.set_state(AddAdmin.uid)

@router.message(AddAdmin.uid)
async def add_finish(m: Message, state: FSMContext):
    try:
        uid = int(m.text)
        set_role(uid, "admin")
        await m.answer("✅ Admin qo‘shildi")
    except:
        await m.answer("❌ Noto‘g‘ri ID")

    await state.clear()

# ================= DELETE ADMIN =================
@router.message(F.text == "➖ Admin o‘chirish")
async def del_start(m: Message, state: FSMContext):
    if m.from_user.id != SUPER_ADMIN:
        return

    await m.answer("🆔 O‘chiriladigan admin ID:")
    await state.set_state(DeleteAdmin.uid)

@router.message(DeleteAdmin.uid)
async def del_finish(m: Message, state: FSMContext):
    try:
        uid = int(m.text)

        if uid == SUPER_ADMIN:
            return await m.answer("❌ Super adminni o‘chira olmaysiz")

        delete_admin(uid)
        await m.answer("🗑 Admin o‘chirildi")

    except:
        await m.answer("❌ Xatolik")

    await state.clear()

# ================= JAVOB =================
@router.callback_query(F.data.startswith("ans:"))
async def answer_start(call: CallbackQuery, state: FSMContext):
    await call.answer()

    if not is_admin(call.from_user.id):
        return

    cid = call.data.split(":")[1]

    await state.update_data(cid=cid)
    await call.message.answer("👤 Ism familiya:")
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
    await m.answer("📝 Javob matni:")
    await state.set_state(Answer.text)

@router.message(Answer.text)
async def a4(m: Message, state: FSMContext):
    data = await state.get_data()
    cid = data["cid"]

    ap = get_appeal(cid)
    if not ap:
        return

    text = f"""📨 <b>RASMИЙ JAVOB</b>

🆔 {cid}

👤 {data['name']}
💼 {data['job']}
📞 {data['phone']}

📝 {m.text}

📌 33-modda asosida:
Yuqori organlarga murojaat qilish huquqiga egasiz.

🏢 Xo‘jaobod suv ta’minoti
📍 Navoiy MFY, Obihayot 1-uy
"""

    await m.bot.send_message(ap["user_id"], text)
    await m.answer("✅ Yuborildi")
    await state.clear()

# ================= QABUL =================
@router.callback_query(F.data.startswith("ok:"))
async def ok(call: CallbackQuery):
    await call.answer()

    if not is_admin(call.from_user.id):
        return

    cid = call.data.split(":")[1]
    ap = get_appeal(cid)

    update_status(cid, "Jarayonda")

    await call.bot.send_message(ap["user_id"], f"⏳ Jarayonda\n🆔 {cid}")
    await call.message.answer("✅ Qabul qilindi")

# ================= RAD =================
@router.callback_query(F.data.startswith("no:"))
async def reject_start(call: CallbackQuery, state: FSMContext):
    await call.answer()

    if not is_admin(call.from_user.id):
        return

    cid = call.data.split(":")[1]

    await state.update_data(cid=cid)
    await call.message.answer("❌ Rad sababini yozing:")
    await state.set_state(Reject.reason)

@router.message(Reject.reason)
async def reject_finish(m: Message, state: FSMContext):
    data = await state.get_data()
    cid = data["cid"]

    ap = get_appeal(cid)

    update_status(cid, "Rad etildi")

    await m.bot.send_message(
        ap["user_id"],
        f"❌ Rad etildi\n🆔 {cid}\nSabab: {m.text}"
    )

    await m.answer("❌ Rad etildi")
    await state.clear()
