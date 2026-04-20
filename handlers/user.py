from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import add_appeal, get_appeal, get_admins
from handlers.admin import buttons

router = Router()

# 🔥 LOCK (parallel muammo yo‘q)
processing = set()

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
    await state.clear()
    await m.answer("👤 Ism Familya:", reply_markup=back_btn())
    await state.set_state(Form.name)

@router.message(Form.name)
async def m2(m: Message, state: FSMContext):
    await state.update_data(name=m.text)
    await m.answer("📞 Telefon:", reply_markup=phone_btn())
    await state.set_state(Form.phone)

@router.message(Form.phone)
async def m3(m: Message, state: FSMContext):
    phone = m.contact.phone_number if m.contact else m.text
    username = m.from_user.username or "yo‘q"

    await state.update_data(phone=phone, username=username)
    await m.answer("📍 Manzil:", reply_markup=location_btn())
    await state.set_state(Form.address)

@router.message(Form.address)
async def m4(m: Message, state: FSMContext):
    address = (
        f"{m.location.latitude},{m.location.longitude}"
        if m.location else m.text
    )

    await state.update_data(address=address)
    await m.answer("📝 Murojaat:", reply_markup=back_btn())
    await state.set_state(Form.message)

# ================= YUBORISH =================
@router.message(Form.message)
async def m5(m: Message, state: FSMContext):
    if m.from_user.id in processing:
        return

    processing.add(m.from_user.id)

    try:
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
👤 @{data['username']}
📍 {data['address']}
📝 {m.text}
"""

        # 🔥 ADMIN SAFE
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
            f"""✅ <b>Qabul qilindi</b>
🆔 {cid}

📌 Javob tez orada beriladi
""",
            reply_markup=menu()
        )

        await state.clear()

    except Exception as e:
        print("ERROR USER:", e)

    finally:
        processing.discard(m.from_user.id)

# ================= TEKSHIRISH =================
@router.message(F.text == "🔍 Tekshirish")
async def c1(m: Message, state: FSMContext):
    await m.answer("🆔 ID kiriting:", reply_markup=back_btn())
    await state.set_state(Check.cid)

@router.message(Check.cid)
async def c2(m: Message, state: FSMContext):
    try:
        ap = get_appeal(m.text.strip())

        if ap:
            # 🔥 SAFE INDEX
            status = ap[6] if len(ap) > 6 else "Noma'lum"
            await m.answer(f"📊 Status: {status}", reply_markup=menu())
        else:
            await m.answer("❌ Topilmadi", reply_markup=menu())

    except Exception as e:
        print("ERROR CHECK:", e)

    await state.clear()
