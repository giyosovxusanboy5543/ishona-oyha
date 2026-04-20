from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import add_appeal, get_appeal, get_admins
from handlers.admin import buttons

router = Router()

# ================= MENU =================
def menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📩 Murojaat")],
            [KeyboardButton(text="🔍 Tekshirish")],
            [KeyboardButton(text="📍 Bizning manzil")]
        ],
        resize_keyboard=True
    )

def back_btn():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Orqaga")]],
        resize_keyboard=True
    )

def phone_btn():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Telefon yuborish", request_contact=True)],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )

def location_btn():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Lokatsiya yuborish", request_location=True)],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )

# ================= STATES =================
class Form(StatesGroup):
    name = State()
    phone = State()
    address = State()
    message = State()

class Check(StatesGroup):
    cid = State()

# ================= START =================
@router.message(Command("start"))
async def start(m: Message):
    await m.answer("Xizmatni tanlang:", reply_markup=menu())

# ================= ORQAGA =================
@router.message(F.text == "⬅️ Orqaga")
async def back(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Bosh menu", reply_markup=menu())

# ================= MANZIL =================
@router.message(F.text == "📍 Bizning manzil")
async def location_info(m: Message):
    await m.answer("📍 Xo‘jaobod tumani, Navoiy MFY,\nObihayot ko‘chasi, 1-uy")

# ================= MUROJAAT =================
@router.message(F.text == "📩 Murojaat")
async def m1(m: Message, state: FSMContext):
    await state.clear()  # 🔥 SERVER UCHUN MUHIM
    await m.answer("👤 Ism Familya:", reply_markup=back_btn())
    await state.set_state(Form.name)

@router.message(Form.name)
async def m2(m: Message, state: FSMContext):
    await state.update_data(name=m.text)
    await m.answer("📞 Telefon yuboring:", reply_markup=phone_btn())
    await state.set_state(Form.phone)

# ================= TELEFON =================
@router.message(Form.phone)
async def m3(m: Message, state: FSMContext):
    if m.contact:
        phone = m.contact.phone_number
    else:
        phone = m.text

    username = m.from_user.username or "yo‘q"

    await state.update_data(phone=phone, username=username)
    await m.answer("📍 Manzil yuboring:", reply_markup=location_btn())
    await state.set_state(Form.address)

# ================= MANZIL =================
@router.message(Form.address)
async def m4(m: Message, state: FSMContext):
    if m.location:
        address = f"{m.location.latitude}, {m.location.longitude}"
    else:
        address = m.text

    await state.update_data(address=address)
    await m.answer("📝 Murojaat matni:", reply_markup=back_btn())
    await state.set_state(Form.message)

# ================= YUBORISH =================
@router.message(Form.message)
async def m5(m: Message, state: FSMContext):
    data = await state.get_data()

    cid = add_appeal((
        m.from_user.id,
        data["name"],
        data["phone"],
        data["address"],
        m.text
    ))

    text = f"""📢 <b>YANGI MUROJAAT</b>
🆔 {cid}

👤 {data['name']}
📞 {data['phone']}
👤 Username: @{data['username']}
📍 {data['address']}
📝 {m.text}
"""

    # 🔥 SERVER SAFE (BOT YIQILMAYDI)
    for admin in get_admins():
        try:
            await m.bot.send_message(
                admin,
                text,
                reply_markup=buttons(cid)
            )
        except Exception as e:
            print("ADMIN ERROR:", e)

    await m.answer(
        f"""✅ <b>Murojaatingiz qabul qilindi</b>
🆔 {cid}

📌 15–30 ish kun ichida javob beriladi.
🙏 Rahmat!
""",
        reply_markup=menu()
    )

    await state.clear()

# ================= TEKSHIRISH =================
@router.message(F.text == "🔍 Tekshirish")
async def c1(m: Message, state: FSMContext):
    await m.answer("🆔 ID kiriting:", reply_markup=back_btn())
    await state.set_state(Check.cid)

@router.message(Check.cid)
async def c2(m: Message, state: FSMContext):
    ap = get_appeal(m.text)

    if ap:
        await m.answer(f"📊 Status: {ap[7]}", reply_markup=menu())
    else:
        await m.answer("❌ Topilmadi", reply_markup=menu())

    await state.clear()
