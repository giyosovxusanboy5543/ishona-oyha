from aiogram import Router, F
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import (
    get_appeal,
    update_status,
    get_admins,
    set_role,
    delete_admin
)

router = Router()
SUPER_ADMIN = 2034709966

# ================= CHECK =================
def is_admin(uid):
    return uid in get_admins()

# ================= INLINE BUTTON =================
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

class Reject(StatesGroup):
    cid = State()
    reason = State()

class Answer(StatesGroup):
    cid = State()
    name = State()
    job = State()
    phone = State()
    text = State()
    file = State()

# =================================================
# ================= SUPER ADMIN ====================
# =================================================

# -------- ADD ADMIN --------
@router.message(Command("add"))
async def add_start(m: Message, state: FSMContext):
    if m.from_user.id != SUPER_ADMIN:
        return

    await m.answer("🆔 Admin ID yuboring:")
    await state.set_state(AddAdmin.uid)

@router.message(AddAdmin.uid)
async def add_finish(m: Message, state: FSMContext):
    if m.from_user.id != SUPER_ADMIN:
        return

    try:
        uid = int(m.text)

        if uid == SUPER_ADMIN:
            return await m.answer("❌ Siz allaqachon super adminsiz")

        set_role(uid, "admin")

        await m.answer(f"✅ Admin qo‘shildi\n🆔 {uid}")

    except:
        await m.answer("❌ Noto‘g‘ri ID")

    await state.clear()

# -------- DELETE ADMIN --------
@router.message(Command("del"))
async def del_start(m: Message, state: FSMContext):
    if m.from_user.id != SUPER_ADMIN:
        return

    await m.answer("🆔 O‘chiriladigan admin ID:")
    await state.set_state(DeleteAdmin.uid)

@router.message(DeleteAdmin.uid)
async def del_finish(m: Message, state: FSMContext):
    if m.from_user.id != SUPER_ADMIN:
        return

    try:
        uid = int(m.text)

        if uid == SUPER_ADMIN:
            return await m.answer("❌ Super adminni o‘chira olmaysiz")

        delete_admin(uid)
        await m.answer(f"🗑 Admin o‘chirildi\n🆔 {uid}")

    except:
        await m.answer("❌ Xatolik")

    await state.clear()

# -------- ADMIN LIST --------
@router.message(Command("admins"))
async def admin_list(m: Message):
    if m.from_user.id != SUPER_ADMIN:
        return

    admins = get_admins()

    if not admins:
        return await m.answer("❌ Admin yo‘q")

    text = "📋 Adminlar:\n\n"

    for uid in admins:
        role = "👑 Super Admin" if uid == SUPER_ADMIN else "👨‍💼 Admin"
        text += f"{role}\n🆔 {uid}\n\n"

    await m.answer(text)

# =================================================
# ================= MUROJAAT =======================
# =================================================

# -------- QABUL --------
@router.callback_query(F.data.startswith("ok:"))
async def ok(call: CallbackQuery):
    await call.answer()

    if not is_admin(call.from_user.id):
        return

    cid = call.data.split(":")[1]
    ap = get_appeal(cid)

    if not ap:
        return

    update_status(cid, "Jarayonda")

    await call.bot.send_message(
        ap["user_id"],
        f"""✅ Murojaatingiz qabul qilindi

🆔 {cid}
📌 Holat: Jarayonda

Xo‘jaobod tumani suv ta’minoti AJ"""
    )

    await call.message.answer("✅ Qabul qilindi")

# -------- RAD --------
@router.callback_query(F.data.startswith("no:"))
async def reject_start(call: CallbackQuery, state: FSMContext):
    await call.answer()

    if not is_admin(call.from_user.id):
        return

    cid = call.data.split(":")[1]

    await state.update_data(cid=cid)
    await call.message.answer("❗ Rad etish sababini yozing:")
    await state.set_state(Reject.reason)

@router.message(Reject.reason)
async def reject_finish(m: Message, state: FSMContext):
    data = await state.get_data()
    cid = data["cid"]

    ap = get_appeal(cid)
    if not ap:
        return

    update_status(cid, "Rad etildi")

    await m.bot.send_message(
        ap["user_id"],
        f"""❌ Murojaat rad etildi

🆔 {cid}

📌 Sabab:
{m.text}"""
    )

    await m.answer("❌ Rad etildi")
    await state.clear()

# -------- JAVOB --------
@router.callback_query(F.data.startswith("ans:"))
async def answer_start(call: CallbackQuery, state: FSMContext):
    await call.answer()

    if not is_admin(call.from_user.id):
        return

    cid = call.data.split(":")[1]

    await state.clear()
    await state.update_data(cid=cid)

    await call.message.answer("👤 Mutaxassis F.I.O:")
    await state.set_state(Answer.name)

@router.message(Answer.name)
async def a1(m: Message, state: FSMContext):
    await state.update_data(name=m.text)
    await m.answer("💼 Lavozimi:")
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
    await state.update_data(text=m.text)
    await m.answer("📎 Fayl yuboring (majburiy):")
    await state.set_state(Answer.file)

@router.message(Answer.file)
async def a5(m: Message, state: FSMContext):
    if not (m.document or m.photo):
        return await m.answer("❗ Fayl yuborish majburiy")

    data = await state.get_data()
    cid = data["cid"]

    ap = get_appeal(cid)
    if not ap:
        return

    text = f"""📨 RASMІY JAVOB

🆔 {cid}

👤 {data['name']}
💼 {data['job']}
📞 {data['phone']}

📝 {data['text']}

📌 33-modda:
Yuqori organlarga murojaat qilish huquqiga egasiz.

🏢 Xo‘jaobod suv ta’minoti AJ
📍 Navoiy MFY, Obihayot 1-uy
"""

    await m.bot.send_message(ap["user_id"], text)

    if m.document:
        await m.bot.send_document(ap["user_id"], m.document.file_id)
    else:
        await m.bot.send_photo(ap["user_id"], m.photo[-1].file_id)

    await m.answer("✅ Javob yuborildi")
    await state.clear()
