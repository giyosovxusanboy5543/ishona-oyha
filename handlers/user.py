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

# ================= MENU =================
def menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📩 Murojaat")],
            [KeyboardButton(text="🔍 Murojaat holati")],
            [
                KeyboardButton(text="📍 Bizning manzil"),
                KeyboardButton(text="📞 Telefon yuborish", request_contact=True)
            ]
        ],
        resize_keyboard=True
    )

# ================= STATES =================
class Form(StatesGroup):
    name = State()
    address = State()
    phone = State()
    message = State()
    file = State()

class Check(StatesGroup):
    cid = State()

# ================= START =================
@router.message(Command("start"))
async def start(m: Message):
    await m.answer(
        "👋 Xush kelibsiz!\nKerakli bo‘limni tanlang:",
        reply_markup=menu()
    )

# ================= MANZIL =================
@router.message(F.text == "📍 Bizning manzil")
async def location(m: Message):
    await m.answer(
        "📍 Xo‘jaobod tumani suv ta’minoti\n\n"
        "🏢 Navoiy MFY, Obihayot ko‘chasi 1-uy"
    )

# ================= CONTACT =================
@router.message(F.contact)
async def contact_handler(m: Message):
    await m.answer(f"📞 Raqamingiz qabul qilindi: {m.contact.phone_number}")

# ================= MUROJAAT BOSHLASH =================
@router.message(F.text == "📩 Murojaat")
async def start_form(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("👤 Ismingiz:\n\nMisol: <b>Bobur Qobulov</b>")
    await state.set_state(Form.name)

@router.message(Form.name)
async def get_name(m: Message, state: FSMContext):
    await state.update_data(name=m.text)
    await m.answer("📍 Manzil (MFY):\nMisol: Bobur MFY, Olima ko‘chasi 9-uy")
    await state.set_state(Form.address)

@router.message(Form.address)
async def get_address(m: Message, state: FSMContext):
    await state.update_data(address=m.text)
    await m.answer("📞 Telefon raqamingizni yuboring yoki yozing")
    await state.set_state(Form.phone)

@router.message(Form.phone)
async def get_phone(m: Message, state: FSMContext):
    phone = m.contact.phone_number if m.contact else m.text
    await state.update_data(phone=phone)

    # 🔥 NAMUNA SHU YERDA
    await m.answer(
        "📝 Murojaat matnini yozing\n\n"
        "Quyidagi namuna asosida yozing:\n\n"
        "🔹 Muammo turi:\n"
        "🔹 Muammo manzili:\n"
        "🔹 Tavsif:\n\n"
        "📌 Misol:\n\n"
        "Muammo turi: Suv bosimi past\n"
        "Manzil: Bobur MFY, Olima ko‘chasi 9-uy\n"
        "Tavsif: Oxirgi 3 kundan beri suv past kelmoqda\n\n"
        "✍️ Iltimos, aniq yozing"
    )

    await state.set_state(Form.message)

@router.message(Form.message)
async def get_message(m: Message, state: FSMContext):
    await state.update_data(message=m.text)
    await m.answer("📎 Fayl yuboring yoki 'yo‘q' deb yozing")
    await state.set_state(Form.file)

# ================= FINAL =================
@router.message(Form.file)
async def finish(m: Message, state: FSMContext):
    if m.from_user.id in processing:
        return

    processing.add(m.from_user.id)

    try:
        data = await state.get_data()

        # 🔥 ID GENERATSIYA
        random_id = random.randint(10000, 99999)
        year = datetime.now().year % 100
        cid = f"{random_id}-r/{year}"

        add_appeal((
            m.from_user.id,
            data["name"],
            data["phone"],
            data["address"],
            data["message"]
        ))

        now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

        text = f"""📢 <b>YANGI MUROJAAT</b>

🆔 {cid}
🕒 {now}

👤 {data['name']}
📍 {data['address']}
📞 {data['phone']}

📝 {data['message']}
"""

        for admin in get_admins():
            try:
                await m.bot.send_message(admin, text, reply_markup=buttons(cid))

                if m.document:
                    await m.bot.send_document(admin, m.document.file_id)
                elif m.photo:
                    await m.bot.send_photo(admin, m.photo[-1].file_id)

            except Exception as e:
                print("ADMIN ERROR:", e)

        await m.answer(f"""✅ Murojaatingiz qabul qilindi

🆔 ID: {cid}

📅 Ko‘rib chiqish muddati:
15 kundan 30 kungacha

📌 Xo‘jaobod tumani suv ta’minoti tomonidan ko‘rib chiqiladi.

📍 Bizning manzil:
Navoiy MFY, Obihayot ko‘chasi 1-uy

🙏 Sabringiz uchun rahmat!""")

        await state.clear()

    except Exception as e:
        print("ERROR:", e)

    finally:
        processing.discard(m.from_user.id)

# ================= HOLAT =================
@router.message(F.text == "🔍 Murojaat holati")
async def check_start(m: Message, state: FSMContext):
    await m.answer("🆔 Murojaat ID sini kiriting:")
    await state.set_state(Check.cid)

@router.message(Check.cid)
async def check_result(m: Message, state: FSMContext):
    ap = get_appeal(m.text)

    if not ap:
        return await m.answer("❌ Murojaat topilmadi")

    await m.answer(f"""📊 MUROJAAT HOLATI

🆔 {m.text}
📌 Status: {ap['status']}
""")

    await state.clear()
