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

# ================= UX MENU =================
def menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📩 Murojaat yuborish")],
            [
                KeyboardButton(text="🔍 Holat tekshirish"),
                KeyboardButton(text="📍 Manzil")
            ],
            [
                KeyboardButton(text="📞 Raqam yuborish", request_contact=True)
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Kerakli bo‘limni tanlang 👇"
    )

# ================= STATES =================
class Form(StatesGroup):
    name = State()
    address = State()
    phone = State()
    message = State()

class Check(StatesGroup):
    cid = State()

# ================= START =================
@router.message(Command("start"))
async def start(m: Message):
    await m.answer(
        "👋 Assalomu alaykum!\n\n"
        "Xo‘jaobod suv ta’minoti botiga xush kelibsiz.\n"
        "Quyidagi menyudan foydalaning 👇",
        reply_markup=menu()
    )

# ================= MANZIL =================
@router.message(F.text == "📍 Manzil")
async def location(m: Message):
    await m.answer(
        "📍 <b>Bizning manzil:</b>\n\n"
        "🏢 Navoiy MFY\n"
        "📌 Obihayot ko‘chasi 1-uy"
    )

# ================= CONTACT =================
@router.message(F.contact)
async def contact_handler(m: Message, state: FSMContext):
    await state.update_data(phone=m.contact.phone_number)
    await m.answer("✅ Raqamingiz qabul qilindi")

# ================= MUROJAAT BOSHLASH =================
@router.message(F.text == "📩 Murojaat yuborish")
async def start_form(m: Message, state: FSMContext):
    await state.clear()

    await m.answer(
        "👤 <b>Ism familiyangizni kiriting</b>\n\n"
        "Masalan: <i>Bobur Qobulov</i>"
    )

    await state.set_state(Form.name)

@router.message(Form.name)
async def get_name(m: Message, state: FSMContext):
    await state.update_data(name=m.text)

    await m.answer(
        "📍 <b>Manzilingizni kiriting</b>\n\n"
        "Masalan:\n<i>Bobur MFY, Olima ko‘chasi 9-uy</i>"
    )

    await state.set_state(Form.address)

@router.message(Form.address)
async def get_address(m: Message, state: FSMContext):
    await state.update_data(address=m.text)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Raqam yuborish", request_contact=True)]
        ],
        resize_keyboard=True
    )

    await m.answer(
        "📞 <b>Telefon raqamingizni yuboring</b>\n"
        "yoki yozib kiriting",
        reply_markup=kb
    )

    await state.set_state(Form.phone)

@router.message(Form.phone)
async def get_phone(m: Message, state: FSMContext):
    phone = m.contact.phone_number if m.contact else m.text
    await state.update_data(phone=phone)

    await m.answer(
        "📝 <b>Muammo haqida yozing</b>\n\n"
        "Masalan:\n"
        "Suv bosimi past, 3 kundan beri muammo bor"
    )

    await state.set_state(Form.message)

# ================= FINAL =================
@router.message(Form.message)
async def finish(m: Message, state: FSMContext):
    if m.from_user.id in processing:
        return

    processing.add(m.from_user.id)

    try:
        data = await state.get_data()

        # UNIQUE ID
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
        ))

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

🆔 ID: <b>{cid}</b>
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
@router.message(F.text == "🔍 Holat tekshirish")
async def check_start(m: Message, state: FSMContext):
    await m.answer("🆔 ID ni kiriting:")
    await state.set_state(Check.cid)

@router.message(Check.cid)
async def check_result(m: Message, state: FSMContext):
    ap = get_appeal(m.text)

    if not ap:
        return await m.answer("❌ Murojaat topilmadi")

    await m.answer(
        f"""📊 <b>Murojaat holati</b>

🆔 {m.text}
📌 Status: <b>{ap['status']}</b>
""",
        reply_markup=menu()
    )

    await state.clear()
