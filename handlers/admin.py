from aiogram import Router, F
from aiogram.types import *
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import get_appeal, update_status, get_admins, set_role

router = Router()
processing = set()

# 🔥 SUPER ADMIN ID
SUPER_ADMIN = 2034709966

# ================= ADMIN CHECK =================
def is_admin(uid):
    return uid in get_admins()

# ================= BUTTONS =================
def buttons(cid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Qabul", callback_data=f"ok_{cid}"),
            InlineKeyboardButton(text="❌ Rad", callback_data=f"no_{cid}")
        ],
        [
            InlineKeyboardButton(text="✉️ Javob", callback_data=f"ans_{cid}")
        ]
    ])

# ================= STATES =================
class AddAdmin(StatesGroup):
    uid = State()

class Answer(StatesGroup):
    cid = State()
    name = State()
    job = State()
    phone = State()
    text = State()
    file = State()

class Reject(StatesGroup):
    cid = State()
    reason = State()

# ================= ADMIN PANEL =================
@router.message(F.text == "⚙️ Admin panel")
async def admin_panel(m: Message):
    if m.from_user.id != SUPER_ADMIN:
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Admin qo‘shish")],
            [KeyboardButton(text="❌ Admin o‘chirish")]
        ],
        resize_keyboard=True
    )

    await m.answer("⚙️ Admin panel", reply_markup=kb)

# ================= ADD ADMIN =================
@router.message(F.text == "➕ Admin qo‘shish")
async def add_admin_start(m: Message, state: FSMContext):
    if m.from_user.id != SUPER_ADMIN:
        return

    await m.answer("🆔 Telegram ID yuboring:")
    await state.set_state(AddAdmin.uid)

@router.message(AddAdmin.uid)
async def add_admin_finish(m: Message, state: FSMContext):
    try:
        uid = int(m.text)
        set_role(uid, "admin")
        await m.answer("✅ Admin qo‘shildi")
    except:
        await m.answer("❌ Noto‘g‘ri ID")

    await state.clear()

# ================= DELETE ADMIN =================
@router.message(F.text == "❌ Admin o‘chirish")
async def delete_admin(m: Message):
    await m.answer("⚠️ Bu funksiya db.py da yozilishi kerak")

# ================= JAVOB BOSHLASH =================
@router.callback_query(F.data.startswith("ans_"))
async def answer_start(call: CallbackQuery, state: FSMContext):
    await call.answer()

    if call.from_user.id in processing:
        return

    processing.add(call.from_user.id)

    try:
        if not is_admin(call.from_user.id):
            return

        cid = call.data.split("_")[1]
        ap = get_appeal(cid)

        if not ap:
            return

        await state.clear()
        await state.update_data(cid=cid)

        await call.message.answer("👤 Mutaxassis ism familiya:")
        await state.set_state(Answer.name)

    finally:
        processing.discard(call.from_user.id)

# ================= JAVOB BOSQICHLARI =================
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
    await state.update_data(text=m.text)
    await m.answer("📎 Fayl yuborish (ixtiyoriy)")
    await state.set_state(Answer.file)

# ================= JAVOB YUBORISH =================
@router.message(Answer.file)
async def a5(m: Message, state: FSMContext):
    data = await state.get_data()
    cid = data["cid"]

    ap = get_appeal(cid)
    if not ap:
        return

    text = f"""📨 <b>RASMИЙ JAVOB</b>

🆔 {cid}

👤 Mutaxassis: {data['name']}
💼 Lavozimi: {data['job']}
📞 Telefon: {data['phone']}

📝 {data['text']}

📌 Eslatma:
Mazkur javobdan norozi bo‘lgan taqdiringizda yuqori turuvchi organlarga murojaat qilish huquqiga egasiz.

🏢 Hurmat bilan,
Xo‘jaobod tumani suv ta’minoti AJ

📍 Manzil:
Navoiy MFY, Obihayot ko‘chasi 1-uy
"""

    await m.bot.send_message(ap["user_id"], text)

    if m.document:
        await m.bot.send_document(ap["user_id"], m.document.file_id)
    elif m.photo:
        await m.bot.send_photo(ap["user_id"], m.photo[-1].file_id)

    await m.answer("✅ Javob yuborildi")
    await state.clear()

# ================= QABUL =================
@router.callback_query(F.data.startswith("ok_"))
async def ok(call: CallbackQuery):
    await call.answer()

    if not is_admin(call.from_user.id):
        return

    cid = call.data.split("_")[1]
    ap = get_appeal(cid)

    if not ap:
        return

    update_status(cid, "Jarayonda")

    await call.bot.send_message(
        ap["user_id"],
        f"⏳ Murojaatingiz ko‘rib chiqilmoqda\n🆔 {cid}"
    )

    await call.message.answer("✅ Qabul qilindi")

# ================= RAD =================
@router.callback_query(F.data.startswith("no_"))
async def reject_start(call: CallbackQuery, state: FSMContext):
    await call.answer()

    if not is_admin(call.from_user.id):
        return

    cid = call.data.split("_")[1]

    await state.update_data(cid=cid)
    await call.message.answer("❌ Rad sababini yozing:")
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
        f"""❌ Murojaatingiz rad etildi

🆔 {cid}

📌 Sabab:
{m.text}
"""
    )

    await m.answer("❌ Rad etildi")
    await state.clear()
