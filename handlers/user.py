from aiogram import Router, F
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import random

from db import add_appeal, get_admins, get_appeal
from handlers.admin import buttons

router = Router()
processing = set()

# ================= MENU (UX DESIGN) =================
def menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📩 Murojaat yuborish")],
            [
                KeyboardButton(text="🔍 Murojaat holatini tekshirish"),
                KeyboardButton(text="📍 Bizning manzil")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Kerakli bo‘limni tanlang 👇"
    )

def back_btn():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Orqaga")]],
        resize_keyboard=True
    )

# ================= STATES =================
class Form(StatesGroup):
    name = State()
    address = State()
    phone = State()
    message = State()

class Check(StatesGroup):
    cid = State()

# ================= START (PRO DESIGN) =================
@router.message(Command("start"))
async def start(m: Message):
    await m.answer(
        f"""🏢 <b>Xo‘jaobod tumani suv ta’minoti AJ</b>

📢 <b>Rasmiy murojaat qabul qilish boti</b>

━━━━━━━━━━━━━━━━━━━

👋 Assalomu alaykum!

Ushbu bot orqali siz:

📩 Murojaat yuborishingiz  
🔍 Murojaatingiz holatini tekshirishingiz  
📍 Bizning manzilni bilishingiz mumkin  

━━━━━━━━━━━━━━━━━━━

📌 <b>Eslatma:</b>
Murojaatlar qonunchilik asosida 15–30 kun ichida ko‘rib chiqiladi.

👇 Davom etish uchun menyudan tanlang""",
        reply_markup=menu()
    )

# ================= BACK =================
@router.message(F.text == "⬅️ Orqaga")
async def back(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("🔙 Asosiy menyu", reply_markup=menu())

# ================= MANZIL =================
@router.message(F.text == "📍 Bizning manzil")
async def location(m: Message):
    await m.answer(
        """📍 <b>Bizning manzil:</b>

🏢 Xo‘jaobod tumani
📌 Navoiy MFY
📍 Obihayot ko‘chasi 1-uy"""
    )

# ================= MUROJAAT =================
@router.message(F.text == "📩 Murojaat yuborish")
async def start_form(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("👤 Ism familiyangizni kiriting:", reply_markup=back_btn())
    await state.set_state(Form.name)

@router.message(Form.name)
async def get_name(m: Message, state: FSMContext):
    await state.update_data(name=m.text)
    await m.answer("📍 Manzilingizni kiriting:", reply_markup=back_btn())
    await state.set_state(Form.address)

@router.message(Form.address)
async def get_address(m: Message, state: FSMContext):
    await state.update_data(address=m.text)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Raqam yuborish", request_contact=True)],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )

    await m.answer("📞 Telefon raqamingizni yuboring:", reply_markup=kb)
    await state.set_state(Form.phone)

# 🔥 CONTACT FIX
@router.message(Form.phone, F.contact)
async def contact_handler(m: Message, state: FSMContext):
    await state.update_data(phone=m.contact.phone_number)
    await m.answer("📝 Muammo haqida yozing:", reply_markup=back_btn())
    await state.set_state(Form.message)

@router.message(Form.phone)
async def get_phone(m: Message, state: FSMContext):
    await state.update_data(phone=m.text)
    await m.answer("📝 Muammo haqida yozing:", reply_markup=back_btn())
    await state.set_state(Form.message)

# ================= FINAL =================
@router.message(Form.message)
async def finish(m: Message, state: FSMContext):
    if m.from_user.id in processing:
        return

    processing.add(m.from_user.id)

    try:
        data = await state.get_data()

        rand = random.randint(10000, 99999)
        year = datetime.now().year % 100
        cid = f"{rand}-r/{year}"

        now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

        add_appeal((
            m.from_user.id,
            data["name"],
            data["phone"],
            data["address"],
            m.text
        ), cid)

        text = f"""📢 <b>YANGI MUROJAAT</b>

🆔 {cid}
🕒 {now}

👤 {data['name']}
📍 {data['address']}
📞 {data['phone']}

📝 {m.text}
"""

        for admin in get_admins():
            await m.bot.send_message(admin, text, reply_markup=buttons(cid))

        await m.answer(
            f"""✅ <b>Murojaatingiz qabul qilindi</b>

🆔 {cid}
🕒 {now}

📅 Ko‘rib chiqish muddati:
15–30 kun

📍 Manzil:
Navoiy MFY, Obihayot ko‘chasi 1-uy

🙏 Rahmat!""",
            reply_markup=menu()
        )

        await state.clear()

    finally:
        processing.discard(m.from_user.id)

# ================= TEKSHIRISH =================
@router.message(F.text == "🔍 Murojaat holatini tekshirish")
async def check_start(m: Message, state: FSMContext):
    await m.answer("🆔 ID kiriting:", reply_markup=back_btn())
    await state.set_state(Check.cid)

@router.message(Check.cid)
async def check_result(m: Message, state: FSMContext):
    ap = get_appeal(m.text.strip())

    if not ap:
        return await m.answer("❌ Murojaat topilmadi", reply_markup=menu())

    await m.answer(
        f"""📊 <b>Murojaat holati</b>

🆔 {ap['cid']}
📌 Status: {ap['status']}
🕒 {ap['created']}
""",
        reply_markup=menu()
    )

    await state.clear()
