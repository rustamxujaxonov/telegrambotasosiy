import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import update_user, get_user, is_premium
from keyboards import (
    gender_keyboard, regions_keyboard,
    settings_keyboard, main_menu_keyboard
)

router = Router()
logger = logging.getLogger(__name__)


class SettingsState(StatesGroup):
    edit_age = State()


# ─── JINSNI O'ZGARTIRISH ────────────────────────────────────────────────────────

@router.callback_query(F.data == "edit_gender")
async def edit_gender_prompt(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔄 <b>Yangi jinsingizni tanlang:</b>",
        reply_markup=gender_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.in_(["gender_male", "gender_female"]))
async def edit_gender_save(callback: CallbackQuery, state: FSMContext):
    # Agar registration holati bo'lsa — registration handler ish ko'radi
    current_state = await state.get_state()
    if current_state and "RegState" in current_state:
        return
    
    # Foydalanuvchi ro'yxatdan o'tganmi?
    user = await get_user(callback.from_user.id)
    if not user:
        return  # Registration handler ish ko'radi
    
    gender = "male" if callback.data == "gender_male" else "female"
    gender_text = "👦 Yigit" if gender == "male" else "👧 Qiz"
    
    await update_user(callback.from_user.id, gender=gender)
    
    premium = await is_premium(callback.from_user.id)
    await callback.message.edit_text(
        f"✅ <b>Jins yangilandi: {gender_text}</b>"
    )
    await callback.message.answer(
        "⚙️ Profil sozlamalari:",
        reply_markup=settings_keyboard()
    )
    await callback.answer()


# ─── YOSHNI O'ZGARTIRISH ────────────────────────────────────────────────────────

@router.callback_query(F.data == "edit_age")
async def edit_age_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsState.edit_age)
    await callback.message.edit_text(
        "🔢 <b>Yangi yoshingizni kiriting:</b>\n"
        "<i>(14 dan 60 gacha raqam)</i>"
    )
    await callback.answer()


@router.message(SettingsState.edit_age)
async def edit_age_save(message: Message, state: FSMContext):
    try:
        age = int(message.text.strip())
    except ValueError:
        await message.answer("❗ Faqat raqam kiriting. Masalan: 22")
        return
    
    if age < 14 or age > 60:
        await message.answer("❗ Yosh 14 dan 60 gacha bo'lishi kerak:")
        return
    
    await update_user(message.from_user.id, age=age)
    await state.clear()
    
    await message.answer(
        f"✅ <b>Yosh yangilandi: {age}</b>\n\n"
        f"Profil sozlamalari:",
        reply_markup=settings_keyboard()
    )


# ─── VILOYATNI O'ZGARTIRISH ─────────────────────────────────────────────────────

@router.callback_query(F.data == "edit_region")
async def edit_region_prompt(callback: CallbackQuery):
    await callback.message.edit_text(
        "📍 <b>Yangi viloyatingizni tanlang:</b>",
        reply_markup=regions_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("region_"))
async def edit_region_save(callback: CallbackQuery, state: FSMContext):
    # Agar registration state bo'lsa — u yerda handle qilinadi
    current_state = await state.get_state()
    if current_state and "RegState" in current_state:
        return
    
    user = await get_user(callback.from_user.id)
    if not user:
        return
    
    region = callback.data.replace("region_", "")
    await update_user(callback.from_user.id, region=region)
    
    await callback.message.edit_text(
        f"✅ <b>Viloyat yangilandi: {region}</b>"
    )
    await callback.message.answer(
        "⚙️ Profil sozlamalari:",
        reply_markup=settings_keyboard()
    )
    await callback.answer()
