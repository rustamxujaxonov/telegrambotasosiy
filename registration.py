import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import create_user, is_premium
from keyboards import (
    gender_keyboard, regions_keyboard,
    main_menu_keyboard
)

router = Router()
logger = logging.getLogger(__name__)


class RegState(StatesGroup):
    gender = State()
    full_name = State()
    age = State()
    region = State()


async def start_registration(message: Message, user_id: int):
    """Ro'yxatdan o'tishni boshlash"""
    await message.answer(
        "1️⃣ <b>Jinsingizni tanlang:</b>",
        reply_markup=gender_keyboard()
    )


@router.callback_query(F.data.in_(["gender_male", "gender_female"]))
async def reg_gender(callback: CallbackQuery, state: FSMContext):
    # Agar allaqachon ro'yxatdan o'tgan bo'lsa — settings'dan kelayotgan bo'lishi mumkin
    current_state = await state.get_state()
    
    gender = "male" if callback.data == "gender_male" else "female"
    gender_text = "👦 Yigit" if gender == "male" else "👧 Qiz"
    
    await state.update_data(gender=gender)
    await callback.message.edit_text(
        f"✅ Jins: <b>{gender_text}</b>\n\n"
        f"2️⃣ <b>Ism va familiyangizni kiriting:</b>\n"
        f"<i>(Masalan: Alisher Karimov)</i>"
    )
    await state.set_state(RegState.full_name)
    await callback.answer()


@router.message(RegState.full_name)
async def reg_name(message: Message, state: FSMContext):
    name = message.text.strip()
    
    if len(name) < 3:
        await message.answer("❗ Ism juda qisqa. Kamida 3 ta harf kiriting:")
        return
    
    if len(name) > 50:
        await message.answer("❗ Ism juda uzun. 50 ta harfdan kam kiriting:")
        return
    
    await state.update_data(full_name=name)
    await message.answer(
        f"✅ Ism: <b>{name}</b>\n\n"
        f"3️⃣ <b>Yoshingizni kiriting:</b>\n"
        f"<i>(Faqat raqam, masalan: 21)</i>"
    )
    await state.set_state(RegState.age)


@router.message(RegState.age)
async def reg_age(message: Message, state: FSMContext):
    try:
        age = int(message.text.strip())
    except ValueError:
        await message.answer("❗ Faqat raqam kiriting. Masalan: 21")
        return
    
    if age < 14 or age > 60:
        await message.answer("❗ Yosh 14 dan 60 gacha bo'lishi kerak:")
        return
    
    await state.update_data(age=age)
    await message.answer(
        f"✅ Yosh: <b>{age}</b>\n\n"
        f"4️⃣ <b>Viloyatingizni tanlang:</b>",
        reply_markup=regions_keyboard()
    )
    await state.set_state(RegState.region)


@router.callback_query(RegState.region, F.data.startswith("region_"))
async def reg_region(callback: CallbackQuery, state: FSMContext, bot: Bot):
    region = callback.data.replace("region_", "")
    data = await state.get_data()
    
    user_id = callback.from_user.id
    username = callback.from_user.username or ""
    
    # Ma'lumotlarni saqlash
    await create_user(
        user_id=user_id,
        username=username,
        full_name=data["full_name"],
        age=data["age"],
        gender=data["gender"],
        region=region
    )
    
    await state.clear()
    
    gender_emoji = "👦" if data["gender"] == "male" else "👧"
    premium = await is_premium(user_id)
    
    await callback.message.edit_text(
        f"🎊 <b>Ro'yxatdan o'tdingiz!</b>\n\n"
        f"👤 Ism: <b>{data['full_name']}</b>\n"
        f"{gender_emoji} Jins: <b>{'Yigit' if data['gender'] == 'male' else 'Qiz'}</b>\n"
        f"🎂 Yosh: <b>{data['age']}</b>\n"
        f"📍 Viloyat: <b>{region}</b>\n\n"
        f"✅ Endi botdan to'liq foydalanishingiz mumkin!"
    )
    
    await callback.message.answer(
        "🏠 <b>Asosiy menyu</b>\n\nQuyidagi tugmalardan birini tanlang:",
        reply_markup=main_menu_keyboard(premium)
    )
    await callback.answer()
