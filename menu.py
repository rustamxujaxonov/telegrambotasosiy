import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import CHANNEL_ID
from database import get_user, is_premium
from keyboards import main_menu_keyboard, settings_keyboard
from utils import is_subscribed, require_registration

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "👤 Mening profilim")
async def my_profile(message: Message):
    user = await get_user(message.from_user.id)
    if not await require_registration(message, user):
        return
    
    premium = await is_premium(message.from_user.id)
    gender_text = "👦 Yigit" if user["gender"] == "male" else "👧 Qiz"
    premium_text = "✅ Premium" if premium else "❌ Oddiy"
    
    until_text = ""
    if premium and user["premium_until"]:
        from datetime import datetime
        until = datetime.fromisoformat(user["premium_until"])
        until_text = f"\n⏳ Premium muddat: <b>{until.strftime('%d.%m.%Y %H:%M')}</b>"
    
    await message.answer(
        f"👤 <b>Mening profilim</b>\n\n"
        f"📝 Ism: <b>{user['full_name']}</b>\n"
        f"{gender_text}: <b>{'Yigit' if user['gender'] == 'male' else 'Qiz'}</b>\n"
        f"🎂 Yosh: <b>{user['age']}</b>\n"
        f"📍 Viloyat: <b>{user['region']}</b>\n"
        f"💎 Status: <b>{premium_text}</b>{until_text}"
    )


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    premium = await is_premium(callback.from_user.id)
    
    await callback.message.answer(
        "🏠 <b>Asosiy menyu</b>",
        reply_markup=main_menu_keyboard(premium)
    )
    await callback.answer()


@router.message(F.text == "⚙️ Profil sozlamalari")
async def profile_settings(message: Message):
    user = await get_user(message.from_user.id)
    if not await require_registration(message, user):
        return
    
    gender_text = "👦 Yigit" if user["gender"] == "male" else "👧 Qiz"
    
    await message.answer(
        f"⚙️ <b>Profil sozlamalari</b>\n\n"
        f"Hozirgi ma'lumotlar:\n"
        f"📝 Ism: <b>{user['full_name']}</b>\n"
        f"{gender_text}\n"
        f"🎂 Yosh: <b>{user['age']}</b>\n"
        f"📍 Viloyat: <b>{user['region']}</b>\n\n"
        f"Nimani o'zgartirmoqchisiz?",
        reply_markup=settings_keyboard()
    )
