from aiogram import Router, F
from aiogram.types import *
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import get_appeal, update_status, set_role, get_role, get_admins

router = Router()

# 🔥 O‘ZINGNI ID ING
SUPER_ADMIN = 2034709966


# ================= TUGMALAR =================
def buttons(cid):
    cid = str(cid).strip()
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Qabul", callback_data=f"ok_{cid}")],
        [InlineKeyboardButton(text="✉️ Javob", callback_data=f"ans_{cid}")],
        [InlineKeyboardButton(text="❌ Rad", callback_data=f"no_{cid}")]
    ])


# ================= STATES =================
class Answer(StatesGroup):
    cid = State()
    name = State()
    job = State()
    phone = State()
    file = State()


class Reject(StatesGroup):
    cid = State()
    reason = State()


# ================= ADMIN TEKSHIRUV =================
def is_admin(user_id):
    role = get_role(user_id)
    return role in ("admin", "super_admin") or user_id == SUPER_ADMIN


def is_super_admin(user_id):
    return user_id == SUPER_ADMIN or get_role(user_id) == "super_admin"


# ================= JAVOB =================
@router.callback_query(F.data.startswith("ans_"))
async def answer_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer("❌ Ruxsat yo‘q", show_alert=True)

    cid = call.data.split("_", 1)[1].strip()
    ap = get_appeal(cid)

    if not ap:
        return await call.message.answer("❌ Topilmadi")

    await state.update_data(cid=cid)
    await call.message.answer("👤 Ism familya:")
    await state.set_state(Answer.name)


@router.message(Answer.name)
async def a1(m: Message, state: FSMContext):
    await state.update_data(name=m.text.strip())
    await m.answer("💼 Lavozim:")
    await state.set_state(Answer.job)


@router.message(Answer.job)
async def a2(m: Message, state: FSMContext):
    await state.update_data(job=m.text.strip())
    await m.answer("📞 Telefon:")
    await state.set_state(Answer.phone)


@router.message(Answer.phone)
async def a3(m: Message, state: FSMContext):
    await state.update_data(phone=m.text.strip())
    await m.answer("📎 Fayl yuboring (majburiy)")
    await state.set_state(Answer.file)


@router.message(Answer.file)
async def a4(m: Message, state: FSMContext):
    data = await state.get_data()
    cid = str(data["cid"]).strip()

    ap = get_appeal(cid)
    if not ap:
        return await m.answer("❌ Topilmadi")

    if not m.document and not m.photo:
        return await m.answer("❗ Fayl yuborish majburiy!")

    text = f"""📨 JAVOB
🆔 {cid}

👤 {data['name']}
💼 {data['job']}
📞 {data['phone']}

👨‍💼 Javob berdi: {m.from_user.id}
"""

    await m.bot.send_message(ap[2], text)

    if m.document:
        await m.bot.send_document(ap[2], m.document.file_id)
    elif m.photo:
        await m.bot.send_photo(ap[2], m.photo[-1].file_id)

    update_status(cid, "Yakunlandi")

    await m.answer("✅ Javob yuborildi")
    await state.clear()


# ================= QABUL =================
@router.callback_query(F.data.startswith("ok_"))
async def ok(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("❌ Ruxsat yo‘q", show_alert=True)

    cid = call.data.split("_", 1)[1].strip()
    ap = get_appeal(cid)

    if not ap:
        return await call.message.answer("❌ Topilmadi")

    update_status(cid, f"Jarayonda ({call.from_user.id})")

    await call.bot.send_message(
        ap[2],
        f"⏳ Murojaatingiz jarayonda\n🆔 {cid}"
    )

    await call.message.answer("✅ Qabul qilindi")


# ================= RAD =================
@router.callback_query(F.data.startswith("no_"))
async def no_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer("❌ Ruxsat yo‘q", show_alert=True)

    cid = call.data.split("_", 1)[1].strip()
    ap = get_appeal(cid)

    if not ap:
        return await call.message.answer("❌ Topilmadi")

    await state.update_data(cid=cid)
    await call.message.answer("❗ Rad etish sababini yozing:")
    await state.set_state(Reject.reason)


@router.message(Reject.reason)
async def no_done(m: Message, state: FSMContext):
    data = await state.get_data()
    cid = str(data["cid"]).strip()

    ap = get_appeal(cid)
    if not ap:
        return await m.answer("❌ Topilmadi")

    update_status(cid, "Rad etildi")

    await m.bot.send_message(
        ap[2],
        f"""❌ MUROJAAT RAD ETILDI
🆔 {cid}

📌 Sabab:
{m.text}

👨‍💼 Rad etdi: {m.from_user.id}
"""
    )

    await m.answer("✅ Rad etildi")
    await state.clear()


# ================= PANEL =================
@router.message(F.text == "/panel")
async def panel(m: Message):
    if not is_super_admin(m.from_user.id):
        return await m.answer("❌ Ruxsat yo‘q")

    await m.answer(
        "👑 SUPER ADMIN PANEL\n\n"
        "/add_admin ID\n"
        "/del_admin ID\n"
        "/list_admin"
    )


# ================= ADMIN QO‘SHISH =================
@router.message(F.text.startswith("/add_admin"))
async def add_admin(m: Message):
    if not is_super_admin(m.from_user.id):
        return await m.answer("❌ Ruxsat yo‘q")

    try:
        uid = int(m.text.split()[1])
        set_role(uid, "admin")
        await m.answer(f"✅ Admin qo‘shildi\nID: {uid}")
    except:
        await m.answer("❌ Format: /add_admin 123456789")


# ================= ADMIN O‘CHIRISH =================
@router.message(F.text.startswith("/del_admin"))
async def del_admin(m: Message):
    if not is_super_admin(m.from_user.id):
        return await m.answer("❌ Ruxsat yo‘q")

    try:
        uid = int(m.text.split()[1])
        set_role(uid, "user")
        await m.answer(f"❌ Admin o‘chirildi\nID: {uid}")
    except:
        await m.answer("❌ Format: /del_admin 123456789")


# ================= ADMIN RO‘YXATI =================
@router.message(F.text == "/list_admin")
async def list_admin(m: Message):
    if not is_super_admin(m.from_user.id):
        return

    admins = get_admins()

    if not admins:
        return await m.answer("Admin yo‘q")

    text = "📋 Adminlar:\n\n"
    for i in admins:
        text += f"{i}\n"

    await m.answer(text)
