from aiogram import Router, F
from aiogram.types import *
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import add_appeal, get_admins
from handlers.admin import buttons

router = Router()
processing = set()

# ================= MENU =================
def menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📩 Murojaat")],
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

# ================= START =================
@router.message(Command("start"))
async def start(m: Message):
    await m.answer("📩 Murojaat yuborish uchun tugmani bosing", reply_markup=menu())

# ================= BOSHLASH =================
@router.message(F.text == "📩 Murojaat")
async def start_form(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("👤 Ismingizni kiriting\n\nMisol: <b>Bobur Qobulov</b>")
    await state.set_state(Form.name)

# ================= ISM =================
@router.message(Form.name)
async def get_name(m: Message, state: FSMContext):
    await state.update_data(name=m.text)
    await m.answer(
        "📍 Qaysi MFY va manzilda yashaysiz?\n\n"
        "Misol:\n<b>Bobur MFY, Olima ko‘chasi 9-uy</b>"
    )
    await state.set_state(Form.address)

# ================= MANZIL =================
@router.message(Form.address)
async def get_address(m: Message, state: FSMContext):
    await state.update_data(address=m.text)
    await m.answer("📞 Telefon raqamingizni yuboring yoki yozing")
    await state.set_state(Form.phone)

# ================= TELEFON =================
@router.message(Form.phone)
async def get_phone(m: Message, state: FSMContext):
    phone = m.contact.phone_number if m.contact else m.text
    await state.update_data(phone=phone)

    await m.answer(
        "📝 Murojaat matnini yozing\n\n"
        "Masalan:\n<b>Suv bosimi pastligi haqida murojaat qilaman</b>"
    )
    await state.set_state(Form.message)

# ================= MATN =================
@router.message(Form.message)
async def get_message(m: Message, state: FSMContext):
    await state.update_data(message=m.text)

    await m.answer(
        "📎 Agar fayl biriktirmoqchi bo‘lsangiz yuboring\n\n"
        "Qo‘llab-quvvatlanadi:\n"
        "📄 PDF\n📊 Excel\n📝 Word\n🖼 JPG/PNG\n\n"
        "❌ Agar yo‘q bo‘lsa 'yo‘q' deb yozing"
    )
    await state.set_state(Form.file)

# ================= FILE =================
@router.message(Form.file)
async def finish(m: Message, state: FSMContext):
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
            data["message"]
        ))

        text = f"""📢 <b>YANGI MUROJAAT</b>
🆔 {cid}

👤 {data['name']}
📍 {data['address']}
📞 {data['phone']}

📝 {data['message']}
"""

        # 🔥 ADMINLARGA YUBORISH
        for admin in get_admins():
            try:
                msg = await m.bot.send_message(admin, text, reply_markup=buttons(cid))

                # FILE YUBORISH
                if m.document:
                    await m.bot.send_document(admin, m.document.file_id)
                elif m.photo:
                    await m.bot.send_photo(admin, m.photo[-1].file_id)

            except Exception as e:
                print("ADMIN ERROR:", e)

        await m.answer(f"✅ Murojaatingiz qabul qilindi\n🆔 ID: {cid}")

        await state.clear()

    except Exception as e:
        print("ERROR:", e)

    finally:
        processing.discard(m.from_user.id)
